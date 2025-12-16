"""
SUPPLY CHAIN QUERY PARSER
Converts user questions into JSON query instructions.
Does NOT execute - only parses intent.
Does NOT calculate - only specifies what to calculate.
"""

import json
import re
from typing import Dict, Any, List, Optional


class QueryParser:
    """Parse natural language into JSON query instructions"""
    
    VALID_FIELDS = {
        'shipment_id', 'source_location', 'destination_location',
        'departed_at', 'expected_arrival', 'arrived_at', 'status',
        'sku', 'quantity', 'is_delayed', 'delay_days'
    }
    
    VALID_INTENTS = ['DETAILS', 'COUNT', 'UNIQUE_COUNT', 'METRICS', 'TOP_K', 'FILTER']
    
    LOCATIONS = {'US-LAX', 'CN-SHZ', 'TH-BKK', 'UK-LON', 'DE-FRA', 'SG-SIN', 'IN-DEL', 'IN-MUM'}
    
    LOCATION_ALIASES = {
        'lax': 'US-LAX', 'los angeles': 'US-LAX',
        'shz': 'CN-SHZ', 'shenzhen': 'CN-SHZ',
        'bkk': 'TH-BKK', 'bangkok': 'TH-BKK',
        'lon': 'UK-LON', 'london': 'UK-LON',
        'fra': 'DE-FRA', 'frankfurt': 'DE-FRA',
        'sin': 'SG-SIN', 'singapore': 'SG-SIN',
        'del': 'IN-DEL', 'delhi': 'IN-DEL',
        'mum': 'IN-MUM', 'mumbai': 'IN-MUM',
    }
    
    def parse(self, question: str) -> Dict[str, Any]:
        """Convert question to JSON query instruction"""
        
        q = question.lower().strip()
        
        # Detect intent
        intent = self._detect_intent(q)
        
        # Extract filters (but NOT for METRICS/TOP_K unless explicitly needed)
        if intent in ['METRICS', 'TOP_K']:
            # For METRICS and TOP_K, don't extract location filters - analyze entire dataset
            filters = self._extract_specific_filters(q)  # Only shipment ID, SKU, status
        else:
            filters = self._extract_filters(q)
        
        # Extract grouping
        group_by = self._extract_group_by(q)
        
        # Extract metrics
        metrics = self._extract_metrics(q, intent)
        
        # Extract top_k
        top_k = self._extract_top_k(q)
        
        return {
            "intent": intent,
            "filters": filters,
            "group_by": group_by,
            "metrics": metrics,
            "top_k": top_k
        }
    
    def _extract_specific_filters(self, q: str) -> Dict[str, Any]:
        """Extract only specific filters (for METRICS/TOP_K)"""
        
        filters = {}
        
        # Extract shipment ID only
        match = re.search(r'(shp-\d{7})', q)
        if match:
            filters['shipment_id'] = match.group(1).upper()
        
        # Extract SKU only
        match = re.search(r'sku-\d+', q)
        if match:
            filters['sku'] = match.group(0).upper()
        
        return filters
    
    def _detect_intent(self, q: str) -> str:
        """Detect the intent type"""
        
        # DETAILS - asking for specific shipment info
        if 'shp-' in q:
            return 'DETAILS'
        
        # TOP_K - asking for "most", "best", "worst", "problematic"
        if any(word in q for word in ['most delays', 'most problematic', 'worst', 'best route', 'top', 'highest', 'lowest', 'problematic']):
            return 'TOP_K'
        
        # METRICS - asking for rates, percentages, averages, performance
        if any(word in q for word in ['rate', 'percentage', '%', 'average', 'avg', 'mean', 'on-time', 'delivery', 'performance']):
            return 'METRICS'
        
        # UNIQUE_COUNT - asking for unique, distinct, count of
        if any(word in q for word in ['unique', 'distinct', 'how many unique', 'count unique', 'how many routes']):
            return 'UNIQUE_COUNT'
        
        # COUNT - asking for count of something
        if any(word in q for word in ['how many', 'count', 'total']):
            return 'COUNT'
        
        # FILTER - asking to show/list with filters
        if any(word in q for word in ['show', 'list', 'filter', 'where', 'find']):
            return 'FILTER'
        
        # Default
        return 'FILTER'
    
    def _extract_filters(self, q: str) -> Dict[str, Any]:
        """Extract filter conditions"""
        
        filters = {}
        
        # Extract shipment ID
        match = re.search(r'(shp-\d{7})', q)
        if match:
            filters['shipment_id'] = match.group(1).upper()
        
        # Extract location
        location = self._extract_location(q)
        if location:
            if 'from' in q and 'to' in q:
                filters['source_location'] = location if self._is_source(q) else None
                filters['destination_location'] = location if not self._is_source(q) else None
            elif 'from' in q:
                filters['source_location'] = location
            else:
                filters['destination_location'] = location
        
        # Extract status
        status = self._extract_status(q)
        if status:
            filters['status'] = status
        
        # Extract SKU
        match = re.search(r'sku-\d+', q)
        if match:
            filters['sku'] = match.group(0).upper()
        
        # Remove None values
        return {k: v for k, v in filters.items() if v is not None}
    
    def _extract_location(self, q: str) -> Optional[str]:
        """Extract location from question"""
        
        for alias, location in self.LOCATION_ALIASES.items():
            if alias in q:
                return location
        
        # Check for full location codes
        for location in self.LOCATIONS:
            if location.lower() in q:
                return location
        
        return None
    
    def _is_source(self, q: str) -> bool:
        """Check if location is a source"""
        return 'from' in q.split('location')[0] if 'location' in q else 'from' in q[:q.find('location')] if 'location' in q else False
    
    def _extract_status(self, q: str) -> Optional[str]:
        """Extract status filter"""
        
        if 'arrived' in q or 'delivered' in q:
            return 'ARRIVED'
        if 'transit' in q or 'in-transit' in q:
            return 'IN_TRANSIT'
        if 'delayed' in q or 'delay' in q or 'late' in q:
            return 'DELAYED'
        
        return None
    
    def _extract_group_by(self, q: str) -> List[str]:
        """Extract grouping fields"""
        
        group_by = []
        
        if 'by sku' in q or 'per sku' in q or 'sku' in q and 'problematic' in q:
            group_by.append('sku')
        if 'by route' in q or 'per route' in q or 'routes' in q and 'delay' in q:
            group_by.extend(['source_location', 'destination_location'])
        if 'by location' in q or 'per location' in q:
            group_by.append('destination_location')
        if 'by status' in q or 'per status' in q:
            group_by.append('status')
        
        # Default grouping for TOP_K if nothing specified
        if not group_by:
            if 'sku' in q and 'problematic' in q:
                group_by = ['sku']
            else:
                group_by = ['destination_location']
        
        return group_by
    
    def _extract_metrics(self, q: str, intent: str) -> List[str]:
        """Extract which metrics to calculate"""
        
        metrics = []
        
        if intent == 'METRICS':
            if 'delay' in q and 'rate' in q:
                metrics.append('delay_rate')
            if 'on-time' in q or 'ontime' in q or 'on time' in q:
                metrics.append('on_time_rate')
            if 'average' in q or 'avg' in q:
                if 'delay' in q:
                    metrics.append('avg_delay_days')
            if not metrics:
                metrics = ['on_time_rate', 'delay_rate']
        
        if 'count' in q:
            metrics.append('count')
        if 'total' in q and 'units' in q:
            metrics.append('total_quantity')
        
        return metrics
    
    def _extract_top_k(self, q: str) -> Optional[int]:
        """Extract number of top results"""
        
        match = re.search(r'(?:top|best|worst|first)\s+(\d+)', q)
        if match:
            return int(match.group(1))
        
        if 'most' in q or 'worst' in q:
            return 10  # Default to top 10
        
        return None


def parse_query(question: str) -> str:
    """Parse question to JSON instruction"""
    parser = QueryParser()
    result = parser.parse(question)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Test
    parser = QueryParser()
    
    test_queries = [
        "What routes have the most delays?",
        "Which SKUs are problematic?",
        "How many shipments to UK-LON?",
        "What is our on-time delivery rate?",
        "SHP-0000020 details",
    ]
    
    for q in test_queries:
        result = parser.parse(q)
        print(f"Question: {q}")
        print(f"Intent: {json.dumps(result, indent=2)}\n")
