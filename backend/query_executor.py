"""
SUPPLY CHAIN QUERY EXECUTOR
Executes JSON query instructions against CSV data.
Does NOT invent data - returns exactly what's in the CSV.
"""

import pandas as pd
from typing import Dict, Any, List, Optional


class QueryExecutor:
    """Execute JSON query instructions against CSV data"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
    
    def execute(self, query_instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the query instruction"""
        
        intent = query_instruction.get('intent', 'FILTER')
        filters = query_instruction.get('filters', {})
        group_by = query_instruction.get('group_by', [])
        metrics = query_instruction.get('metrics', [])
        top_k = query_instruction.get('top_k')
        
        # Apply filters
        result_df = self._apply_filters(filters)
        
        if len(result_df) == 0:
            return {
                'intent': intent,
                'record_count': 0,
                'data': [],
                'summary': 'No records found matching filters'
            }
        
        # Execute based on intent
        if intent == 'DETAILS':
            return self._execute_details(result_df, filters)
        
        elif intent == 'COUNT':
            return self._execute_count(result_df)
        
        elif intent == 'UNIQUE_COUNT':
            return self._execute_unique_count(result_df, filters)
        
        elif intent == 'METRICS':
            return self._execute_metrics(result_df, filters, metrics)
        
        elif intent == 'TOP_K':
            return self._execute_top_k(result_df, filters, top_k, group_by, metrics)
        
        else:  # FILTER
            return self._execute_filter(result_df)
    
    def _apply_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filter conditions to dataframe"""
        
        result_df = self.df.copy()
        
        for field, value in filters.items():
            if field == 'shipment_id':
                result_df = result_df[result_df['shipment_id'] == value]
            elif field == 'source_location':
                result_df = result_df[result_df['source_location'] == value]
            elif field == 'destination_location':
                result_df = result_df[result_df['destination_location'] == value]
            elif field == 'status':
                result_df = result_df[result_df['status'] == value]
            elif field == 'sku':
                result_df = result_df[result_df['sku'] == value]
        
        return result_df
    
    def _execute_details(self, df: pd.DataFrame, filters: Dict) -> Dict[str, Any]:
        """Return details for specific shipment"""
        
        if len(df) == 0:
            return {
                'intent': 'DETAILS',
                'record_count': 0,
                'data': [],
                'summary': 'Shipment not found'
            }
        
        shipment = df.iloc[0].to_dict()
        
        return {
            'intent': 'DETAILS',
            'record_count': 1,
            'data': [shipment],
            'summary': f"Shipment {shipment.get('shipment_id')}: {shipment.get('sku')} ({shipment.get('quantity')} units) from {shipment.get('source_location')} to {shipment.get('destination_location')}, Status: {shipment.get('status')}"
        }
    
    def _execute_count(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Count records"""
        
        count = len(df)
        
        return {
            'intent': 'COUNT',
            'record_count': count,
            'data': [],
            'summary': f'Total: {count:,} records'
        }
    
    def _execute_unique_count(self, df: pd.DataFrame, filters: Dict) -> Dict[str, Any]:
        """Count unique values"""
        
        unique_skus = df['sku'].nunique()
        unique_routes = len(df.groupby(['source_location', 'destination_location']))
        
        summary = f'Dataset contains {unique_skus} unique SKUs and {unique_routes} unique delivery routes'
        
        return {
            'intent': 'UNIQUE_COUNT',
            'record_count': len(df),
            'unique_skus': unique_skus,
            'unique_routes': unique_routes,
            'data': [],
            'summary': summary
        }
    
    def _execute_metrics(self, df: pd.DataFrame, filters: Dict, metrics: List[str]) -> Dict[str, Any]:
        """Calculate metrics"""
        
        result = {
            'intent': 'METRICS',
            'record_count': len(df),
            'data': [],
            'metrics': {}
        }
        
        # Calculate metrics
        total_shipments = len(df)
        arrived = len(df[df['status'] == 'ARRIVED'])
        
        if arrived > 0:
            on_time = len(df[(df['status'] == 'ARRIVED') & (df['arrived_at'] <= df['expected_arrival'])])
            delayed = arrived - on_time
            
            result['metrics']['on_time_rate'] = round((on_time / arrived) * 100, 2)
            result['metrics']['delay_rate'] = round((delayed / arrived) * 100, 2)
            result['metrics']['avg_delay_days'] = round(df[df['is_delayed'] == True]['delay_days'].mean(), 2) if 'delay_days' in df.columns else 0
        
        result['metrics']['total_shipments'] = total_shipments
        result['metrics']['arrived_shipments'] = arrived
        result['metrics']['in_transit'] = len(df[df['status'] == 'IN_TRANSIT'])
        
        location = filters.get('destination_location', '')
        location_text = f' to {location}' if location else ''
        
        on_time_rate = result['metrics'].get('on_time_rate', 0)
        delay_rate = result['metrics'].get('delay_rate', 0)
        
        result['summary'] = f'Shipment metrics{location_text}: On-time rate: {on_time_rate}%, Delay rate: {delay_rate}%, Total shipments: {total_shipments:,}'
        
        return result
    
    def _execute_top_k(self, df: pd.DataFrame, filters: Dict, top_k: Optional[int], group_by: List[str], metrics: List[str]) -> Dict[str, Any]:
        """Get top K results"""
        
        if not group_by or len(group_by) == 0:
            group_by = ['destination_location']
        
        # Add calculated delay columns
        df_calc = df.copy()
        df_calc['arrived_at'] = pd.to_datetime(df_calc['arrived_at'], errors='coerce')
        df_calc['expected_arrival'] = pd.to_datetime(df_calc['expected_arrival'], errors='coerce')
        df_calc['is_delayed'] = (df_calc['arrived_at'] > df_calc['expected_arrival']) & (df_calc['status'] == 'ARRIVED')
        df_calc['is_delayed'] = df_calc['is_delayed'].fillna(False)
        
        # Group and calculate metrics
        grouped = df_calc.groupby(group_by).agg({
            'shipment_id': 'count',
            'is_delayed': 'sum'
        }).reset_index()
        
        grouped.columns = list(group_by) + ['total_shipments', 'delayed_shipments']
        grouped['delayed_shipments'] = grouped['delayed_shipments'].astype(int)
        
        # Calculate delay rate
        grouped['delay_rate'] = (grouped['delayed_shipments'] / grouped['total_shipments'] * 100).round(2)
        
        # Sort by delay rate (descending)
        grouped = grouped.sort_values('delay_rate', ascending=False)
        
        # Get top K
        k = top_k or 10
        top_results = grouped.head(k)
        
        summary_lines = []
        for idx, row in top_results.iterrows():
            if 'source_location' in group_by:
                route = f"{row.get('source_location', 'N/A')} to {row.get('destination_location', 'N/A')}"
            else:
                route = str(row.get('destination_location', 'N/A'))
            summary_lines.append(f"{route}: {row['delay_rate']}% delay rate ({int(row['delayed_shipments'])} of {int(row['total_shipments'])} delayed)")
        
        return {
            'intent': 'TOP_K',
            'record_count': len(df),
            'top_k': k,
            'data': top_results.to_dict('records'),
            'summary': '\n'.join(summary_lines) if summary_lines else 'No data'
        }
    
    def _execute_filter(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return filtered results"""
        
        count = len(df)
        
        return {
            'intent': 'FILTER',
            'record_count': count,
            'data': df.head(10).to_dict('records'),
            'summary': f'Found {count:,} records'
        }


if __name__ == "__main__":
    # Test
    df = pd.read_csv('shipment_data_1M.csv')
    executor = QueryExecutor(df)
    
    # Test with a query instruction
    instruction = {
        'intent': 'TOP_K',
        'filters': {},
        'group_by': ['destination_location'],
        'metrics': ['delay_rate'],
        'top_k': 5
    }
    
    result = executor.execute(instruction)
    print(f"Result: {result['summary']}")
