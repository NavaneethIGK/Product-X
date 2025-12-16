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
        
        print(f"\nStep 2: Execute Query (Python/Pandas)")
        
        # STEP 2: Execute query using Python/Pandas on actual data
        result_data = self._execute_query_plan(query_plan)
        print(f"  Results: {len(result_data.get('records', []))} records found")
        
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
        
        else:
            return {'count': 0, 'error': f'Unknown operation: {operation}'}
    
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
            return (f"Shipment {shp.get('shipment_id')}: {shp.get('sku')} ({shp.get('quantity')} units), "
                    f"Status: {shp.get('status')}, From {shp.get('source_location')} to {shp.get('destination_location')}")
        
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
        
        else:
            return "No data found."


if __name__ == "__main__":
    print("[OK] Hybrid Query Pipeline Module Loaded")
    print("Pipeline: User → Intent Detection → Data Execution → Validation → Response Formatting")
