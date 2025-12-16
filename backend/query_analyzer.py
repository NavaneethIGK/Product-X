"""
SUPPLY CHAIN ANALYST
Explains query results clearly without inventing data.
"""

from typing import Dict, Any


class QueryAnalyzer:
    """Analyze and explain query results"""
    
    def analyze(self, execution_result: Dict[str, Any]) -> str:
        """Convert execution result to human-readable explanation"""
        
        intent = execution_result.get('intent', 'UNKNOWN')
        record_count = execution_result.get('record_count', 0)
        
        if record_count == 0:
            return f"No data found for the specified criteria."
        
        if intent == 'DETAILS':
            return self._analyze_details(execution_result)
        elif intent == 'COUNT':
            return self._analyze_count(execution_result)
        elif intent == 'UNIQUE_COUNT':
            return self._analyze_unique_count(execution_result)
        elif intent == 'METRICS':
            return self._analyze_metrics(execution_result)
        elif intent == 'TOP_K':
            return self._analyze_top_k(execution_result)
        elif intent == 'FILTER':
            return self._analyze_filter(execution_result)
        else:
            return execution_result.get('summary', 'Unknown result')
    
    def _analyze_details(self, result: Dict[str, Any]) -> str:
        """Analyze DETAILS result"""
        
        if not result['data']:
            return "Shipment details not found."
        
        shipment = result['data'][0]
        
        lines = [f"Shipment {shipment.get('shipment_id', 'N/A')}:"]
        lines.append(f"  Product: {shipment.get('sku', 'N/A')} ({shipment.get('quantity', 0)} units)")
        lines.append(f"  Route: {shipment.get('source_location', 'N/A')} → {shipment.get('destination_location', 'N/A')}")
        lines.append(f"  Status: {shipment.get('status', 'N/A')}")
        
        if shipment.get('departed_at'):
            lines.append(f"  Departed: {shipment.get('departed_at', 'N/A')}")
        if shipment.get('expected_arrival'):
            lines.append(f"  Expected arrival: {shipment.get('expected_arrival', 'N/A')}")
        if shipment.get('arrived_at') and shipment.get('status') == 'ARRIVED':
            lines.append(f"  Actual arrival: {shipment.get('arrived_at', 'N/A')}")
        
        return '\n'.join(lines)
    
    def _analyze_count(self, result: Dict[str, Any]) -> str:
        """Analyze COUNT result"""
        
        count = result.get('record_count', 0)
        return f"Total shipments: {count:,}"
    
    def _analyze_unique_count(self, result: Dict[str, Any]) -> str:
        """Analyze UNIQUE_COUNT result"""
        
        unique_skus = result.get('unique_skus', 0)
        unique_routes = result.get('unique_routes', 0)
        
        return f"Dataset contains {unique_skus} unique SKUs and {unique_routes} unique delivery routes across {result.get('record_count', 0):,} shipments."
    
    def _analyze_metrics(self, result: Dict[str, Any]) -> str:
        """Analyze METRICS result"""
        
        metrics = result.get('metrics', {})
        
        lines = ["Shipment Performance Metrics:"]
        
        if 'on_time_rate' in metrics:
            lines.append(f"  On-time delivery rate: {metrics['on_time_rate']}%")
        if 'delay_rate' in metrics:
            lines.append(f"  Delay rate: {metrics['delay_rate']}%")
        if 'avg_delay_days' in metrics and metrics['avg_delay_days'] > 0:
            lines.append(f"  Average delay: {metrics['avg_delay_days']} days")
        
        lines.append(f"  Total shipments: {metrics.get('total_shipments', 0):,}")
        lines.append(f"  Arrived: {metrics.get('arrived_shipments', 0):,}")
        lines.append(f"  In transit: {metrics.get('in_transit', 0):,}")
        
        return '\n'.join(lines)
    
    def _analyze_top_k(self, result: Dict[str, Any]) -> str:
        """Analyze TOP_K result"""
        
        data = result.get('data', [])
        
        if not data:
            return "No routes found with delay data."
        
        lines = [f"Top routes with most delays (showing top {result.get('top_k', len(data))}):\n"]
        
        for idx, row in enumerate(data, 1):
            source = row.get('source_location', 'N/A')
            dest = row.get('destination_location', 'N/A')
            delay_rate = row.get('delay_rate', 0)
            delayed_count = int(row.get('delayed_shipments', 0))
            total_count = int(row.get('total_shipments', 0))
            
            if source and source != 'N/A':
                route = f"{source} → {dest}"
            else:
                route = dest
            
            lines.append(f"{idx}. {route}")
            lines.append(f"   Delay rate: {delay_rate}% ({delayed_count} of {total_count} shipments delayed)")
        
        return '\n'.join(lines)
    
    def _analyze_filter(self, result: Dict[str, Any]) -> str:
        """Analyze FILTER result"""
        
        count = result.get('record_count', 0)
        data = result.get('data', [])
        
        lines = [f"Found {count:,} matching shipments"]
        
        if data:
            lines.append("\nSample records:")
            for shipment in data[:3]:
                lines.append(f"  - {shipment.get('shipment_id', 'N/A')}: {shipment.get('sku', 'N/A')} to {shipment.get('destination_location', 'N/A')} ({shipment.get('status', 'N/A')})")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # Test
    analyzer = QueryAnalyzer()
    
    # Test result
    test_result = {
        'intent': 'METRICS',
        'record_count': 1000000,
        'metrics': {
            'on_time_rate': 38.82,
            'delay_rate': 61.18,
            'avg_delay_days': 2.5,
            'total_shipments': 1000000,
            'arrived_shipments': 699926,
            'in_transit': 300074
        }
    }
    
    analysis = analyzer.analyze(test_result)
    print(analysis)
