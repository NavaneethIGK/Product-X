"""
SMART QUERY ENGINE - Intelligent, Data-Driven Query Interpreter
Automatically detects intent (aggregation, filtering, sorting) based on natural language
"""

import pandas as pd
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# DATA LOADING & CACHING
# ============================================================================

_csv_data = None

def load_data() -> pd.DataFrame:
    """Load CSV once and cache it"""
    global _csv_data
    
    if _csv_data is not None:
        return _csv_data
    
    # Find CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "shipment_data_1M.csv")
    
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    
    try:
        _csv_data = pd.read_csv(csv_path)
        return _csv_data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

# ============================================================================
# INTENT DETECTION - Smart, Keyword-Based
# ============================================================================

class SortOrder(Enum):
    """Sort direction"""
    ASCENDING = "ascending"   # least, lowest, minimum, fewest
    DESCENDING = "descending"  # most, highest, maximum, best

class AggregationType(Enum):
    """What dimension to aggregate by"""
    DESTINATION = "destination"
    SOURCE = "source"
    SKU = "sku"
    ROUTE = "route"
    STATUS = "status"
    FILTER_DESTINATION = "filter_destination"  # NEW: Filter by specific destination
    FILTER_SOURCE = "filter_source"  # NEW: Filter by specific source
    FILTER_SKU = "filter_sku"  # NEW: Filter by specific SKU
    NONE = "none"  # No aggregation needed

@dataclass
class SmartIntent:
    """Parsed user intent with all relevant parameters"""
    aggregation: AggregationType
    sort_order: SortOrder
    limit: int = 10
    filters: Dict[str, Any] = None
    confidence: float = 0.0
    raw_query: str = ""

def detect_sort_order(query: str) -> SortOrder:
    """Detect if user wants least or most"""
    query_lower = query.lower()
    
    # ASCENDING keywords: least, lowest, minimum, fewest, less
    if any(word in query_lower for word in ['least', 'lowest', 'minimum', 'fewest', 'less', 'smallest', 'bottom', 'slowest', 'worst']):
        return SortOrder.ASCENDING
    
    # Default: DESCENDING (most common)
    return SortOrder.DESCENDING

def detect_aggregation_dimension(query: str) -> AggregationType:
    """Detect what dimension to aggregate by"""
    query_lower = query.lower()
    
    # DESTINATION aggregations
    if any(word in query_lower for word in ['destination', 'shipments to', 'orders to', 'which destination', 'ship to', 'shipped to']):
        return AggregationType.DESTINATION
    
    # SOURCE aggregations
    if any(word in query_lower for word in ['source', 'shipments from', 'orders from', 'which source', 'ship from', 'shipped from']):
        return AggregationType.SOURCE
    
    # SKU aggregations
    if any(word in query_lower for word in ['sku', 'product', 'items', 'what sku', 'which sku', 'product code']):
        if any(word in query_lower for word in ['delay', 'slow', 'problem', 'issue', 'performance']):
            return AggregationType.SKU
    
    # ROUTE aggregations (source -> destination combination)
    if any(word in query_lower for word in ['route', 'corridor', 'path', 'lane', 'connection']):
        return AggregationType.ROUTE
    
    # STATUS aggregations
    if any(word in query_lower for word in ['status', 'arrived', 'transit', 'delayed', 'on_time']):
        return AggregationType.STATUS
    
    return AggregationType.NONE

def extract_location_code(query: str) -> Optional[str]:
    """Extract location code from query (e.g., US-LAX, IN-DEL)"""
    # Look for pattern: XX-XXX (2 letters, dash, 3 letters)
    matches = re.findall(r'\b([A-Z]{2}-[A-Z]{3})\b', query)
    if matches:
        return matches[0]  # Return first match
    return None

def extract_sku_code(query: str) -> Optional[str]:
    """Extract SKU code from query (e.g., SKU-0001)"""
    matches = re.findall(r'(SKU-\d+)', query, re.IGNORECASE)
    if matches:
        return matches[0].upper()
    return None

def detect_filter_type(query: str) -> Optional[AggregationType]:
    """Detect if query is filtering by a specific location/SKU"""
    query_lower = query.lower()
    
    # Check for specific destination
    if any(phrase in query_lower for phrase in ['to ', 'towards', 'going to', 'heading to', 'shipped to', 'delivery to']):
        location = extract_location_code(query)
        if location:
            return AggregationType.FILTER_DESTINATION
    
    # Check for specific source
    if any(phrase in query_lower for phrase in ['from ', 'originating from', 'shipped from', 'origin from']):
        location = extract_location_code(query)
        if location:
            return AggregationType.FILTER_SOURCE
    
    # Check for specific SKU
    if 'sku' in query_lower or 'product' in query_lower:
        sku = extract_sku_code(query)
        if sku:
            return AggregationType.FILTER_SKU
    
    return None

def parse_limit(query: str) -> int:
    """Extract limit from query (e.g., "top 5", "show 20")"""
    matches = re.findall(r'\b(\d+)\b', query)
    if matches:
        limit = int(matches[0])
        if 1 <= limit <= 100:
            return limit
    return 10

def smart_parse_intent(user_query: str) -> SmartIntent:
    """Parse user query into structured intent"""
    
    # First check if this is a filter query (specific location/SKU)
    filter_type = detect_filter_type(user_query)
    if filter_type:
        # Extract the specific value
        if filter_type == AggregationType.FILTER_DESTINATION:
            location = extract_location_code(user_query)
            return SmartIntent(
                aggregation=filter_type,
                sort_order=SortOrder.DESCENDING,
                limit=100,  # Return all matching
                filters={'destination': location},
                confidence=0.98,
                raw_query=user_query
            )
        elif filter_type == AggregationType.FILTER_SOURCE:
            location = extract_location_code(user_query)
            return SmartIntent(
                aggregation=filter_type,
                sort_order=SortOrder.DESCENDING,
                limit=100,
                filters={'source': location},
                confidence=0.98,
                raw_query=user_query
            )
        elif filter_type == AggregationType.FILTER_SKU:
            sku = extract_sku_code(user_query)
            return SmartIntent(
                aggregation=filter_type,
                sort_order=SortOrder.DESCENDING,
                limit=100,
                filters={'sku': sku},
                confidence=0.98,
                raw_query=user_query
            )
    
    # Otherwise detect aggregation dimension
    aggregation = detect_aggregation_dimension(user_query)
    sort_order = detect_sort_order(user_query)
    limit = parse_limit(user_query)
    
    # Calculate confidence based on how clear the intent is
    confidence = 0.95 if aggregation != AggregationType.NONE else 0.5
    
    return SmartIntent(
        aggregation=aggregation,
        sort_order=sort_order,
        limit=limit,
        filters={},
        confidence=confidence,
        raw_query=user_query
    )

# ============================================================================
# SMART QUERY EXECUTION
# ============================================================================

def execute_smart_query(intent: SmartIntent) -> Dict[str, Any]:
    """Execute query based on smart intent"""
    
    df = load_data()
    
    if df.empty:
        return {
            "success": False,
            "data": [],
            "summary": "No data available",
            "error": "CSV not loaded"
        }
    
    try:
        # Handle filter queries first
        if intent.aggregation == AggregationType.FILTER_DESTINATION:
            return filter_by_destination(df, intent)
        
        elif intent.aggregation == AggregationType.FILTER_SOURCE:
            return filter_by_source(df, intent)
        
        elif intent.aggregation == AggregationType.FILTER_SKU:
            return filter_by_sku(df, intent)
        
        # Handle aggregation queries
        elif intent.aggregation == AggregationType.DESTINATION:
            return query_by_destination(df, intent)
        
        elif intent.aggregation == AggregationType.SOURCE:
            return query_by_source(df, intent)
        
        elif intent.aggregation == AggregationType.SKU:
            return query_by_sku(df, intent)
        
        elif intent.aggregation == AggregationType.ROUTE:
            return query_by_route(df, intent)
        
        elif intent.aggregation == AggregationType.STATUS:
            return query_by_status(df, intent)
        
        else:
            return {
                "success": False,
                "data": [],
                "summary": "Could not determine query intent",
                "error": "Unknown aggregation type"
            }
    
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "summary": f"Error executing query: {str(e)}",
            "error": str(e)
        }

# ============================================================================
# FILTER QUERIES - Get specific records for a location/SKU
# ============================================================================

def filter_by_destination(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Filter shipments to a specific destination"""
    
    destination = intent.filters.get('destination')
    if not destination:
        return {
            "success": False,
            "data": [],
            "summary": "No destination specified",
            "error": "Missing destination filter"
        }
    
    # Filter by destination
    filtered_df = df[df['destination_location'] == destination]
    
    if filtered_df.empty:
        return {
            "success": True,
            "data": [],
            "summary": f"No shipments found to {destination}",
            "filter_type": "destination",
            "filter_value": destination,
            "total_matching": 0
        }
    
    # Aggregate summary
    summary_data = {
        "destination": destination,
        "total_shipments": len(filtered_df),
        "total_quantity": filtered_df['quantity'].sum(),
        "avg_quantity": float(filtered_df['quantity'].mean()),
        "status_breakdown": filtered_df['status'].value_counts().to_dict(),
        "sku_count": filtered_df['sku'].nunique(),
        "source_locations": filtered_df['source_location'].unique().tolist()
    }
    
    # Return aggregated summary instead of individual records
    results = [summary_data]
    
    return {
        "success": True,
        "data": results,
        "summary": f"{len(filtered_df):,} shipments heading towards {destination}",
        "filter_type": "destination",
        "filter_value": destination,
        "total_matching": len(filtered_df)
    }

def filter_by_source(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Filter shipments from a specific source"""
    
    source = intent.filters.get('source')
    if not source:
        return {
            "success": False,
            "data": [],
            "summary": "No source specified",
            "error": "Missing source filter"
        }
    
    # Filter by source
    filtered_df = df[df['source_location'] == source]
    
    if filtered_df.empty:
        return {
            "success": True,
            "data": [],
            "summary": f"No shipments found from {source}",
            "filter_type": "source",
            "filter_value": source,
            "total_matching": 0
        }
    
    # Aggregate summary
    summary_data = {
        "source": source,
        "total_shipments": len(filtered_df),
        "total_quantity": filtered_df['quantity'].sum(),
        "avg_quantity": float(filtered_df['quantity'].mean()),
        "status_breakdown": filtered_df['status'].value_counts().to_dict(),
        "sku_count": filtered_df['sku'].nunique(),
        "destination_locations": filtered_df['destination_location'].unique().tolist()
    }
    
    results = [summary_data]
    
    return {
        "success": True,
        "data": results,
        "summary": f"{len(filtered_df):,} shipments originating from {source}",
        "filter_type": "source",
        "filter_value": source,
        "total_matching": len(filtered_df)
    }

def filter_by_sku(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Filter shipments for a specific SKU"""
    
    sku = intent.filters.get('sku')
    if not sku:
        return {
            "success": False,
            "data": [],
            "summary": "No SKU specified",
            "error": "Missing SKU filter"
        }
    
    # Filter by SKU
    filtered_df = df[df['sku'] == sku]
    
    if filtered_df.empty:
        return {
            "success": True,
            "data": [],
            "summary": f"No shipments found for {sku}",
            "filter_type": "sku",
            "filter_value": sku,
            "total_matching": 0
        }
    
    # Aggregate summary
    summary_data = {
        "sku": sku,
        "total_shipments": len(filtered_df),
        "total_quantity": filtered_df['quantity'].sum(),
        "avg_quantity": float(filtered_df['quantity'].mean()),
        "status_breakdown": filtered_df['status'].value_counts().to_dict(),
        "source_locations": filtered_df['source_location'].unique().tolist(),
        "destination_locations": filtered_df['destination_location'].unique().tolist()
    }
    
    results = [summary_data]
    
    return {
        "success": True,
        "data": results,
        "summary": f"{len(filtered_df):,} shipments for {sku}",
        "filter_type": "sku",
        "filter_value": sku,
        "total_matching": len(filtered_df)
    }

def query_by_destination(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Aggregate shipments by destination"""
    
    # Count shipments per destination
    dest_counts = df.groupby('destination_location').agg({
        'shipment_id': 'count',
        'quantity': 'sum'
    }).reset_index()
    dest_counts.columns = ['destination', 'shipment_count', 'total_quantity']
    
    # Sort based on intent
    sort_ascending = intent.sort_order == SortOrder.ASCENDING
    dest_counts = dest_counts.sort_values('shipment_count', ascending=sort_ascending)
    
    # Limit results
    results = dest_counts.head(intent.limit).to_dict('records')
    
    order_word = "fewest" if sort_ascending else "most"
    summary = f"Destinations with {order_word} shipments (top {intent.limit})"
    
    return {
        "success": True,
        "data": results,
        "summary": summary,
        "aggregation": "destination",
        "sort_order": intent.sort_order.value,
        "total_unique": len(dest_counts)
    }

def query_by_source(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Aggregate shipments by source"""
    
    source_counts = df.groupby('source_location').agg({
        'shipment_id': 'count',
        'quantity': 'sum'
    }).reset_index()
    source_counts.columns = ['source', 'shipment_count', 'total_quantity']
    
    sort_ascending = intent.sort_order == SortOrder.ASCENDING
    source_counts = source_counts.sort_values('shipment_count', ascending=sort_ascending)
    
    results = source_counts.head(intent.limit).to_dict('records')
    
    order_word = "fewest" if sort_ascending else "most"
    summary = f"Sources with {order_word} shipments (top {intent.limit})"
    
    return {
        "success": True,
        "data": results,
        "summary": summary,
        "aggregation": "source",
        "sort_order": intent.sort_order.value,
        "total_unique": len(source_counts)
    }

def query_by_sku(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Aggregate shipments by SKU"""
    
    sku_counts = df.groupby('sku').agg({
        'shipment_id': 'count',
        'quantity': 'sum'
    }).reset_index()
    sku_counts.columns = ['sku', 'shipment_count', 'total_quantity']
    
    sort_ascending = intent.sort_order == SortOrder.ASCENDING
    sku_counts = sku_counts.sort_values('shipment_count', ascending=sort_ascending)
    
    results = sku_counts.head(intent.limit).to_dict('records')
    
    order_word = "fewest" if sort_ascending else "most"
    summary = f"SKUs with {order_word} shipments (top {intent.limit})"
    
    return {
        "success": True,
        "data": results,
        "summary": summary,
        "aggregation": "sku",
        "sort_order": intent.sort_order.value,
        "total_unique": len(sku_counts)
    }

def query_by_route(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Aggregate shipments by route (source -> destination)"""
    
    route_counts = df.groupby(['source_location', 'destination_location']).agg({
        'shipment_id': 'count',
        'quantity': 'sum'
    }).reset_index()
    route_counts.columns = ['source', 'destination', 'shipment_count', 'total_quantity']
    route_counts['route'] = route_counts['source'] + ' → ' + route_counts['destination']
    
    sort_ascending = intent.sort_order == SortOrder.ASCENDING
    route_counts = route_counts.sort_values('shipment_count', ascending=sort_ascending)
    
    # Keep route column for readability
    results = route_counts[['route', 'shipment_count', 'total_quantity']].head(intent.limit).to_dict('records')
    
    order_word = "fewest" if sort_ascending else "most"
    summary = f"Routes with {order_word} shipments (top {intent.limit})"
    
    return {
        "success": True,
        "data": results,
        "summary": summary,
        "aggregation": "route",
        "sort_order": intent.sort_order.value,
        "total_unique": len(route_counts)
    }

def query_by_status(df: pd.DataFrame, intent: SmartIntent) -> Dict[str, Any]:
    """Aggregate shipments by status"""
    
    status_counts = df.groupby('status').agg({
        'shipment_id': 'count',
        'quantity': 'sum'
    }).reset_index()
    status_counts.columns = ['status', 'shipment_count', 'total_quantity']
    
    sort_ascending = intent.sort_order == SortOrder.ASCENDING
    status_counts = status_counts.sort_values('shipment_count', ascending=sort_ascending)
    
    results = status_counts.to_dict('records')
    
    order_word = "fewest" if sort_ascending else "most"
    summary = f"Shipment status distribution ({order_word} to {order_word.replace('fewest', 'most').replace('most', 'fewest')})"
    
    return {
        "success": True,
        "data": results,
        "summary": summary,
        "aggregation": "status",
        "sort_order": intent.sort_order.value
    }

# ============================================================================
# HUMAN-READABLE FORMATTING
# ============================================================================

def format_for_response(query_result: Dict[str, Any]) -> str:
    """Format query result into concise, human-readable response"""
    
    if not query_result.get("success"):
        return f"❌ {query_result.get('summary', 'Query failed')}"
    
    data = query_result.get("data", [])
    summary = query_result.get("summary", "Query result")
    
    if not data:
        return f"📊 {summary}"
    
    # Check if this is a filter query result
    if query_result.get("filter_type"):
        # Format filter results
        item = data[0]  # Filter results are aggregated
        lines = [f"📊 {summary}"]
        
        if "total_shipments" in item:
            lines.append(f"\n📦 Total Shipments: {item['total_shipments']:,}")
            lines.append(f"📤 Total Quantity: {item['total_quantity']:,} units")
            
            if item['total_quantity'] > 0:
                lines.append(f"📊 Avg per Shipment: {item['avg_quantity']:.1f} units")
            
            if 'status_breakdown' in item and item['status_breakdown']:
                lines.append(f"\n📋 Status Breakdown:")
                for status, count in item['status_breakdown'].items():
                    lines.append(f"   • {status}: {count}")
            
            if query_result.get("filter_type") == "destination":
                if 'source_locations' in item:
                    lines.append(f"\n📍 Origins: {', '.join(item['source_locations'])}")
            
            elif query_result.get("filter_type") == "source":
                if 'destination_locations' in item:
                    lines.append(f"\n🎯 Destinations: {', '.join(item['destination_locations'])}")
            
            if 'sku_count' in item:
                lines.append(f"\n🏷️ Unique SKUs: {item['sku_count']}")
        
        return "\n".join(lines)
    
    # Format as ranked list (for aggregation queries)
    lines = [f"📊 {summary}:"]
    
    for i, item in enumerate(data, 1):
        # Format item based on its structure
        if 'route' in item:
            lines.append(f"  {i}. {item['route']} ({item['shipment_count']} shipments, {item['total_quantity']} units)")
        elif 'destination' in item:
            lines.append(f"  {i}. {item['destination']} ({item['shipment_count']} shipments, {item['total_quantity']} units)")
        elif 'source' in item:
            lines.append(f"  {i}. {item['source']} ({item['shipment_count']} shipments, {item['total_quantity']} units)")
        elif 'sku' in item:
            lines.append(f"  {i}. {item['sku']} ({item['shipment_count']} shipments, {item['total_quantity']} units)")
        elif 'status' in item:
            lines.append(f"  {i}. {item['status']}: {item['shipment_count']} shipments")
    
    return "\n".join(lines)