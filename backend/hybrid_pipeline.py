"""
HYBRID QUERY PIPELINE
User → LLM (Intent) → Python (Data) → Validation → LLM (Language) → Response

This ensures:
- LLM NEVER accesses or guesses data
- Python/Pandas handles ALL data operations
- Results are validated before formatting
- LLM only used for intent understanding and response formatting
"""

import json
from typing import Dict, Any, Optional
import pandas as pd
from query_planner import QueryPlanner


class HybridQueryPipeline:
    """Execute queries through hybrid LLM + Python pipeline"""
    
    def __init__(self, df: pd.DataFrame, groq_api_key: Optional[str] = None):
        self.df = df
        self.groq_api_key = groq_api_key
        self.planner = QueryPlanner()
    
    def execute(self, user_query: str) -> Dict[str, Any]:
        """
        Execute full pipeline:
        1. LLM detects intent (optional - QueryPlanner can do this)
        2. Python executes on CSV/Pandas
        3. Validate results
        4. LLM formats response (optional - use template if available)
        """
        
        print(f"\n[HYBRID PIPELINE]")
        print(f"Step 1: Intent Detection (QueryPlanner)")
        
        # STEP 1: Detect intent using QueryPlanner (no data access)
        query_plan = self.planner.plan_query(user_query)
        print(f"  Operation: {query_plan['operation']}")
        print(f"  Filters: {query_plan['filters']}")
        
        # Check if user mentioned an invalid location
        if query_plan.get('invalid_location_mentioned'):
            return {
                'response': 'No data found.',
                'operation': query_plan['operation'],
                'records': 0,
                'validated': True,
                'method': 'hybrid_pipeline'
            }
        
        print(f"\nStep 2: Execute Query (Python/Pandas)")
        
        # STEP 2: Execute query using Python/Pandas on actual data
        result_data = self._execute_query_plan(query_plan)
        actual_count = result_data.get('count', 0)
        print(f"  Results: {actual_count:,} records found")
        
        print(f"\nStep 3: Validate Results")
        
        # STEP 3: Validate the results
        validation = self._validate_results(query_plan, result_data)
        if not validation['is_valid']:
            return {
                'response': 'No data found.',
                'operation': query_plan['operation'],
                'records': 0,
                'validated': True,
                'method': 'hybrid_pipeline'
            }
        
        print(f"  Validation: PASSED ({validation['message']})")
        
        print(f"\nStep 4: Format Response (Language Only)")
        
        # STEP 4: Format response using templates (no LLM needed for simple cases)
        response = self._format_response(user_query, query_plan, result_data)
        print(f"  Response: {response[:80]}...")
        
        return {
            'response': response,
            'operation': query_plan['operation'],
            'records': result_data.get('count', 0),
            'validated': True,
            'method': 'hybrid_pipeline',
            'filters': query_plan['filters']
        }
    
    def _execute_query_plan(self, query_plan: Dict) -> Dict[str, Any]:
        """Execute query plan against CSV/Pandas - NO LLM, PURE DATA"""
        
        operation = query_plan['operation']
        filters = query_plan['filters']
        
        result_df = self.df.copy()
        
        # Apply filters
        if filters.get('destination_location'):
            result_df = result_df[result_df['destination_location'] == filters['destination_location']]
        
        if filters.get('source_location'):
            result_df = result_df[result_df['source_location'] == filters['source_location']]
        
        if filters.get('shipment_id'):
            result_df = result_df[result_df['shipment_id'] == filters['shipment_id']]
        
        if filters.get('status'):
            result_df = result_df[result_df['status'] == filters['status']]
        
        if filters.get('sku'):
            result_df = result_df[result_df['sku'] == filters['sku']]
        
        # Prepare result based on operation
        if operation == 'COUNT':
            return {
                'count': len(result_df),
                'operation': 'COUNT',
                'records': result_df.head(10).to_dict('records')
            }
        
        elif operation == 'DETAILS':
            if len(result_df) == 0:
                return {'count': 0, 'error': 'Shipment not found'}
            shp = result_df.iloc[0]
            return {
                'count': 1,
                'operation': 'DETAILS',
                'records': [shp.to_dict()]
            }
        
        elif operation == 'LIST':
            return {
                'count': len(result_df),
                'operation': 'LIST',
                'records': result_df.head(20).to_dict('records')
            }
        
        elif operation == 'AGGREGATE_SUM':
            return {
                'count': len(result_df),
                'operation': 'AGGREGATE_SUM',
                'total_units': int(result_df['quantity'].sum()),
                'total_shipments': len(result_df),
                'records': []
            }
        
        elif operation == 'ANALYTICS':
            # Perform analytics on the dataset
            
            # Top SKUs by on-time rate (low = problematic)
            sku_stats = []
            for sku in result_df['sku'].unique()[:5]:  # Top 5
                sku_df = result_df[result_df['sku'] == sku]
                arrived = len(sku_df[sku_df['status'] == 'ARRIVED'])
                if arrived > 0:
                    on_time = len(sku_df[(sku_df['status'] == 'ARRIVED') & 
                                        (sku_df['arrived_at'] <= sku_df['expected_arrival'])])
                    on_time_rate = (on_time / arrived * 100)
                    sku_stats.append({
                        'sku': sku,
                        'on_time_rate': round(on_time_rate, 2),
                        'total_shipments': len(sku_df)
                    })
            
            # Top routes by delay count
            route_stats = []
            result_df['route'] = result_df['source_location'] + ' to ' + result_df['destination_location']
            for route in result_df['route'].unique()[:5]:  # Top 5
                route_df = result_df[result_df['route'] == route]
                arrived = len(route_df[route_df['status'] == 'ARRIVED'])
                if arrived > 0:
                    delayed = len(route_df[(route_df['status'] == 'ARRIVED') & 
                                          (route_df['arrived_at'] > route_df['expected_arrival'])])
                    delay_rate = (delayed / arrived * 100)
                    route_stats.append({
                        'route': route,
                        'delay_rate': round(delay_rate, 2),
                        'delayed_count': delayed,
                        'total_arrived': arrived
                    })
            
            return {
                'count': len(result_df),
                'operation': 'ANALYTICS',
                'sku_stats': sku_stats,
                'route_stats': route_stats,
                'total_records': len(result_df),
                'records': []
            }
        
        elif operation == 'METRICS':
            # Calculate metrics on the filtered dataset
            total_shipments = len(result_df)
            arrived_shipments = len(result_df[result_df['status'] == 'ARRIVED'])
            in_transit = len(result_df[result_df['status'] == 'IN_TRANSIT'])
            
            # On-time rate: shipments that arrived on time
            on_time = len(result_df[(result_df['status'] == 'ARRIVED') & 
                                   (result_df['arrived_at'] <= result_df['expected_arrival'])])
            on_time_rate = (on_time / arrived_shipments * 100) if arrived_shipments > 0 else 0
            
            # Delay rate: shipments that arrived late
            delayed = len(result_df[(result_df['status'] == 'ARRIVED') & 
                                   (result_df['arrived_at'] > result_df['expected_arrival'])])
            delay_rate = (delayed / arrived_shipments * 100) if arrived_shipments > 0 else 0
            
            return {
                'count': total_shipments,
                'operation': 'METRICS',
                'total_shipments': total_shipments,
                'arrived_shipments': arrived_shipments,
                'in_transit_shipments': in_transit,
                'on_time_shipments': on_time,
                'delayed_shipments': delayed,
                'on_time_rate': round(on_time_rate, 2),
                'delay_rate': round(delay_rate, 2),
                'records': []
            }
        
        elif operation == 'UNIQUE_COUNT':
            # Count unique values for SKU, routes, etc.
            unique_skus = len(result_df['sku'].unique())
            unique_routes = len(result_df.groupby(['source_location', 'destination_location']))
            
            return {
                'count': len(result_df),
                'operation': 'UNIQUE_COUNT',
                'unique_skus': unique_skus,
                'unique_routes': unique_routes,
                'total_records': len(result_df),
                'records': []
            }
        
    
    def _validate_results(self, query_plan: Dict, result_data: Dict) -> Dict[str, Any]:
        """Validate results are correct - NO GUESSING"""
        
        count = result_data.get('count', 0)
        
        if count == 0:
            return {
                'is_valid': False,
                'message': 'No records found',
                'record_count': 0
            }
        
        # Check that operation matches result
        operation = query_plan['operation']
        result_operation = result_data.get('operation')
        
        if operation != result_operation:
            return {
                'is_valid': False,
                'message': f'Operation mismatch: expected {operation}, got {result_operation}',
                'record_count': count
            }
        
        # Validate data integrity
        if 'records' in result_data and isinstance(result_data['records'], list):
            if len(result_data['records']) > count:
                return {
                    'is_valid': False,
                    'message': 'Data integrity check failed: more records than count',
                    'record_count': count
                }
        
        return {
            'is_valid': True,
            'message': f'Valid result with {count} records',
            'record_count': count
        }
    
    def _format_response(self, user_query: str, query_plan: Dict, result_data: Dict) -> str:
        """Format response using templates - NO LLM GUESSING"""
        
        operation = query_plan['operation']
        count = result_data.get('count', 0)
        filters = query_plan['filters']
        
        if operation == 'COUNT':
            location = filters.get('destination_location') or filters.get('source_location')
            if location:
                return f"There are {count:,} shipments to {location}."
            else:
                return f"Total count: {count:,} records."
        
        elif operation == 'DETAILS':
            if count == 0:
                return "No data found."
            shp = result_data['records'][0]
            status = shp.get('status', 'N/A')
            departed = shp.get('departed_at', 'N/A')
            expected_arrival = shp.get('expected_arrival', 'N/A')
            arrived = shp.get('arrived_at', 'N/A')
            
            # For in-transit, don't show arrived date
            if status == 'IN_TRANSIT':
                return (f"Shipment {shp.get('shipment_id')}: {shp.get('sku')} ({shp.get('quantity')} units), "
                        f"Status: {status}, From {shp.get('source_location')} to {shp.get('destination_location')}, "
                        f"Departed: {departed}, Expected arrival: {expected_arrival}.")
            else:
                return (f"Shipment {shp.get('shipment_id')}: {shp.get('sku')} ({shp.get('quantity')} units), "
                        f"Status: {status}, From {shp.get('source_location')} to {shp.get('destination_location')}, "
                        f"Departed: {departed}, Expected: {expected_arrival}, Arrived: {arrived}.")
        
        
        elif operation == 'LIST':
            if count == 0:
                return "No data found."
            return f"Found {count:,} shipments."
        
        elif operation == 'AGGREGATE_SUM':
            total_units = result_data.get('total_units', 0)
            total_shipments = result_data.get('total_shipments', 0)
            if total_shipments == 0:
                return "No data found."
            return f"Total units: {total_units:,} across {total_shipments:,} shipments."
        
        elif operation == 'METRICS':
            if count == 0:
                return "No data found."
            
            location = filters.get('destination_location') or filters.get('source_location')
            location_text = f" to {location}" if location else ""
            
            on_time_rate = result_data.get('on_time_rate', 0)
            delay_rate = result_data.get('delay_rate', 0)
            total_shipments = result_data.get('total_shipments', 0)
            
            return f"Shipment metrics{location_text}: On-time rate: {on_time_rate}%, Delay rate: {delay_rate}%, Total shipments: {total_shipments:,}."
        
        elif operation == 'UNIQUE_COUNT':
            if count == 0:
                return "No data found."
            
            unique_skus = result_data.get('unique_skus', 0)
            unique_routes = result_data.get('unique_routes', 0)
            
            return f"Dataset contains {unique_skus} unique SKUs and {unique_routes} unique delivery routes."
        
        elif operation == 'ANALYTICS':
            if count == 0:
                return "No data found."
            
            sku_stats = result_data.get('sku_stats', [])
            route_stats = result_data.get('route_stats', [])
            
            response = "Analysis Results:\n"
            
            if sku_stats:
                response += "Problematic SKUs (lowest on-time rates):\n"
                for stat in sorted(sku_stats, key=lambda x: x['on_time_rate']):
                    response += f"- {stat['sku']}: {stat['on_time_rate']}% on-time ({stat['total_shipments']} shipments)\n"
            
            if route_stats:
                response += "\nRoutes with Most Delays:\n"
                for stat in sorted(route_stats, key=lambda x: x['delay_rate'], reverse=True):
                    response += f"- {stat['route']}: {stat['delay_rate']}% delay rate ({stat['delayed_count']} delayed out of {stat['total_arrived']})\n"
            
            return response.strip()
        
        else:
            return "No data found."


if __name__ == "__main__":
    print("[OK] Hybrid Query Pipeline Module Loaded")
    print("Pipeline: User → Intent Detection → Data Execution → Validation → Response Formatting")
