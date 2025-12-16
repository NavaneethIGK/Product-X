"""
DATA QUERY PLANNER
Converts user questions into JSON query instructions.
Does NOT answer questions - only generates query plans.
"""

import json
import re
from typing import Dict, Any, List, Optional


class QueryPlanner:
    """Convert natural language questions into structured JSON query plans"""
    
    VALID_FIELDS = {
        'shipment_id',
        'source_location',
        'destination_location',
        'status',
        'sku',
        'quantity',
        'departed_at',
        'expected_arrival',
        'arrived_at'
    }
    
    VALID_OPERATIONS = ['COUNT', 'LIST', 'FILTER', 'AGGREGATE_SUM', 'DETAILS', 'METRICS', 'UNIQUE_COUNT', 'ANALYTICS']
    
    VALID_STATUSES = ['ARRIVED', 'IN_TRANSIT', 'DELIVERED', 'DELAYED']
    
    def plan_query(self, user_question: str) -> Dict[str, Any]:
        """
        Convert user question into JSON query instruction.
        Returns dict with operation, filters, and fields.
        """
        
        question_lower = user_question.lower().strip()
        
        # Extract shipment ID (SHP-XXXXXXX)
        shipment_id = self._extract_shipment_id(question_lower)
        
        # Detect operation type
        operation = self._detect_operation(question_lower)
        
        # Extract location references
        locations = self._extract_locations(question_lower)
        
        # Check if user mentioned a location but it's invalid
        # If they asked about "to" or "from" but location is None, mark as invalid
        invalid_location_mentioned = False
        if any(keyword in question_lower for keyword in ['to ', 'from ']) and locations.get('destination') is None and locations.get('source') is None:
            # Check if they actually mentioned a location code/name
            if re.search(r'to\s+([a-z0-9\-]+)', question_lower, re.IGNORECASE) or re.search(r'from\s+([a-z0-9\-]+)', question_lower, re.IGNORECASE):
                invalid_location_mentioned = True
        
        # Extract status references (but NOT for METRICS and DETAILS operations)
        status = self._extract_status(question_lower) if operation not in ['METRICS', 'DETAILS'] else None
        
        # Extract SKU references
        sku = self._extract_sku(question_lower)
        
        # Build query plan
        query_plan = {
            "operation": operation,
            "filters": {
                "shipment_id": shipment_id,
                "source_location": locations.get('source'),
                "destination_location": locations.get('destination'),
                "status": status,
                "sku": sku
            },
            "fields": self._determine_fields(operation, shipment_id),
            "parameters": {
                "limit": self._extract_limit(question_lower),
                "sort_by": self._extract_sort_field(question_lower)
            },
            "invalid_location_mentioned": invalid_location_mentioned
        }
        
        # Remove null filters to keep JSON clean
        query_plan["filters"] = {k: v for k, v in query_plan["filters"].items() if v is not None}
        
        return query_plan
    
    def _extract_shipment_id(self, text: str) -> Optional[str]:
        """Extract shipment ID in format SHP-XXXXXXX"""
        match = re.search(r'(shp-\d{7})', text, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def _detect_operation(self, text: str) -> str:
        """Detect the operation type from question"""
        
        # ANALYTICS operation - asking for insights/analysis (routes with delays, problematic SKUs, etc.)
        if any(word in text for word in ['problematic', 'most delays', 'worst', 'best', 'top', 'bottom', 'analysis', 'insights', 'trending', 'critical']):
            return 'ANALYTICS'
        
        # DETAILS operation - asking for specific shipment info (has SHP-XXXXXXX)
        if 'shp-' in text:
            return 'DETAILS'
        
        # UNIQUE_COUNT operation - asking for distinct/unique counts
        if any(word in text for word in ['unique', 'distinct', 'different', 'how many sku', 'how many routes', 'count of unique']):
            return 'UNIQUE_COUNT'
        
        # METRICS operation - asking for rates (on-time rate, delay rate, performance, etc.)
        if any(word in text for word in ['rate', 'percentage', '%', 'performance', 'metric', 'on-time', 'on time', 'ontime']):
            # Make sure it's asking for rate/metric, not a filter
            if any(word in text for word in ['rate', 'percentage', '%', 'performance', 'metric']):
                return 'METRICS'
        
        # AGGREGATE_SUM operation - asking for sum/total/volume (BEFORE COUNT check)
        if any(word in text for word in ['sum', 'total units', 'volume', 'quantity total', 'total quantity']):
            return 'AGGREGATE_SUM'
        
        # COUNT operation - asking "how many"
        if any(word in text for word in ['how many', 'count', 'total', 'number of']):
            return 'COUNT'
        
        # LIST operation - asking to list/show/get
        if any(word in text for word in ['list', 'show', 'get', 'display', 'all shipments']):
            return 'LIST'
        
        # FILTER operation - asking to filter by criteria
        if any(word in text for word in ['filter', 'where', 'that are', 'which are']):
            return 'FILTER'
        
        # Default to LIST
        return 'LIST'
    
    def _extract_locations(self, text: str) -> Dict[str, Optional[str]]:
        """Extract source and destination locations"""
        
        # Known location codes
        locations_map = {
            'lon': 'UK-LON',
            'lax': 'US-LAX',
            'sfo': 'US-SFO',
            'nyc': 'US-NYC',
            'fra': 'DE-FRA',
            'ams': 'NL-AMS',
            'shz': 'CN-SHZ',
            'bkk': 'TH-BKK',
            'del': 'IN-DEL',
            'mum': 'IN-MUM',
            'sin': 'SG-SIN',
            'uk-lon': 'UK-LON',
            'us-lax': 'US-LAX',
            'in-del': 'IN-DEL',
            'in-mum': 'IN-MUM',
            'cn-shz': 'CN-SHZ',
            'de-fra': 'DE-FRA',
            'th-bkk': 'TH-BKK',
            'sg-sin': 'SG-SIN'
        }
        
        result = {'source': None, 'destination': None}
        
        # List of valid destination locations in the dataset
        valid_locations = {'US-LAX', 'CN-SHZ', 'TH-BKK', 'UK-LON', 'DE-FRA', 'SG-SIN', 'IN-DEL', 'IN-MUM'}
        
        # Look for full location codes first (e.g., CN-SHZ, IN-DEL)
        full_location_match = re.findall(r'([a-z]{2}-[a-z]{3})', text, re.IGNORECASE)
        if full_location_match:
            for loc in full_location_match:
                loc_key = loc.lower()
                if loc_key in locations_map:
                    mapped_loc = locations_map[loc_key]
                    # Only accept if it's a valid location in the dataset
                    if mapped_loc in valid_locations:
                        # First match is usually destination, second is source
                        if result['destination'] is None:
                            result['destination'] = mapped_loc
                        elif result['source'] is None:
                            result['source'] = mapped_loc
        
        # Look for "from X to Y" pattern
        from_to_match = re.search(r'from\s+([a-z0-9\-]+)\s+to\s+([a-z0-9\-]+)', text, re.IGNORECASE)
        if from_to_match:
            source_code = from_to_match.group(1).lower()
            dest_code = from_to_match.group(2).lower()
            source_mapped = locations_map.get(source_code)
            dest_mapped = locations_map.get(dest_code)
            # Only accept if they're valid locations in the dataset
            if source_mapped and source_mapped in valid_locations:
                result['source'] = source_mapped
            if dest_mapped and dest_mapped in valid_locations:
                result['destination'] = dest_mapped
            return result
        
        # Look for "to X" pattern (destination)
        to_match = re.search(r'to\s+([a-z0-9\-]+)', text, re.IGNORECASE)
        if to_match and not result['destination']:
            dest_code = to_match.group(1).lower()
            dest_mapped = locations_map.get(dest_code)
            # Only accept if it's a valid location in the dataset
            if dest_mapped and dest_mapped in valid_locations:
                result['destination'] = dest_mapped
        
        # Look for "from X" pattern (source)
        from_match = re.search(r'from\s+([a-z0-9\-]+)', text, re.IGNORECASE)
        if from_match and not result['source']:
            source_code = from_match.group(1).lower()
            source_mapped = locations_map.get(source_code)
            # Only accept if it's a valid location in the dataset
            if source_mapped and source_mapped in valid_locations:
                result['source'] = source_mapped
        
        return result
    
    def _extract_status(self, text: str) -> Optional[str]:
        """Extract shipment status"""
        
        if any(word in text for word in ['arrived', 'delivered']):
            return 'ARRIVED'
        if any(word in text for word in ['in transit', 'transit', 'in-transit']):
            return 'IN_TRANSIT'
        if any(word in text for word in ['delayed', 'late', 'delay']):
            return 'DELAYED'
        
        return None
    
    def _extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU reference"""
        
        # Look for SKU-XXXX pattern
        match = re.search(r'(sku-\d+)', text, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def _extract_limit(self, text: str) -> Optional[int]:
        """Extract LIMIT if specified"""
        
        # Look for "top X", "first X", "limit X" patterns
        match = re.search(r'(?:top|first|limit|get)\s+(\d+)', text)
        return int(match.group(1)) if match else None
    
    def _extract_sort_field(self, text: str) -> Optional[str]:
        """Extract sort field if specified"""
        
        if 'by date' in text or 'by departure' in text:
            return 'departed_at'
        if 'by arrival' in text or 'by arrived' in text:
            return 'arrived_at'
        if 'by quantity' in text or 'by units' in text:
            return 'quantity'
        if 'by expected' in text:
            return 'expected_arrival'
        
        return None
    
    def _determine_fields(self, operation: str, shipment_id: Optional[str]) -> List[str]:
        """Determine which fields to return based on operation"""
        
        if operation == 'DETAILS':
            # Return all fields for detailed view
            return list(self.VALID_FIELDS)
        
        if operation == 'ANALYTICS':
            # Need all fields for analysis
            return list(self.VALID_FIELDS)
        
        if operation == 'METRICS':
            # Need status and arrival dates for metrics
            return ['shipment_id', 'status', 'expected_arrival', 'arrived_at']
        
        if operation == 'UNIQUE_COUNT':
            # Return all fields to count unique values
            return list(self.VALID_FIELDS)
        
        if operation == 'COUNT':
            # Only need to count, can return minimal fields
            return ['shipment_id']
        
        if operation == 'AGGREGATE_SUM':
            # Need quantity for summing
            return ['shipment_id', 'quantity', 'destination_location', 'source_location']
        
        if operation == 'LIST':
            # Return key fields for list view
            return ['shipment_id', 'sku', 'source_location', 'destination_location', 'status', 'quantity']
        
        if operation == 'FILTER':
            # Return key fields for filtered results
            return ['shipment_id', 'sku', 'source_location', 'destination_location', 'status', 'departed_at']
        
        # Default
        return list(self.VALID_FIELDS)


def plan_user_query(user_question: str) -> str:
    """
    Convert user question to JSON query plan.
    Returns JSON string only - no explanation.
    """
    planner = QueryPlanner()
    query_plan = planner.plan_query(user_question)
    return json.dumps(query_plan, indent=2)


if __name__ == "__main__":
    # Test examples
    test_questions = [
        "how many shipments to IN-DEL?",
        "SHP-0000017",
        "shipments from LON to DEL",
        "total units shipped to US-LAX",
        "list all arrived shipments",
        "filter shipments that are delayed"
    ]
    
    print("[OK] Query Planner Module Loaded")
    print("Supported operations: COUNT, LIST, FILTER, AGGREGATE_SUM, DETAILS")
    print("Valid fields: shipment_id, source_location, destination_location, status, sku, quantity, departed_at, expected_arrival, arrived_at")
