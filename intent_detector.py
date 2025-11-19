"""
NLP Intent Detector - Converts user queries to structured query intents
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class QueryIntent:
    """Parsed user intent"""
    query_type: str  # e.g., 'sku_count', 'delayed_shipments'
    filters: Dict[str, str]  # Optional filters
    limit: int = 10
    confidence: float = 0.0

def detect_intent(user_query: str) -> QueryIntent:
    """Convert natural language query to structured intent"""
    query_lower = user_query.lower().strip()
    
    # SKU COUNT - "how many sku", "total sku", "unique sku"
    if any(phrase in query_lower for phrase in ['how many sku', 'total sku', 'sku count', 'number of sku', 'unique sku', 'different sku', 'total number']):
        return QueryIntent(query_type='sku_count', filters={}, confidence=0.95)
    
    # ORDERS PER SKU - "orders per sku", "which sku have most orders"
    if any(phrase in query_lower for phrase in ['orders per sku', 'order count by sku', 'shipments per sku', 'sku have.*order', 'orders by sku', 'sku.*most order']):
        return QueryIntent(query_type='orders_per_sku', filters={}, limit=10, confidence=0.95)
    
    # TOP ROUTES - "top route", "busiest route", "popular route"
    if any(phrase in query_lower for phrase in ['top route', 'busiest route', 'popular route', 'highest shipment', 'peak route', 'main route']):
        return QueryIntent(query_type='top_routes', filters={}, limit=10, confidence=0.95)
    
    # ROUTE DELAY ANALYSIS - "route" + "delay" or "most" 
    if 'route' in query_lower and any(word in query_lower for word in ['delay', 'most', 'problem']):
        return QueryIntent(query_type='route_delay_analysis', filters={}, limit=10, confidence=0.95)
    
    # PROBLEMATIC ITEMS - catch "problematic" with SKU or general
    if 'problematic' in query_lower:
        if 'sku' in query_lower:
            return QueryIntent(query_type='sku_delay_analysis', filters={}, limit=10, confidence=0.95)
        else:
            return QueryIntent(query_type='summary_stats', filters={}, confidence=0.7)
    
    # SKU DELAY ANALYSIS - "sku" + "delay" or "problem"
    if 'sku' in query_lower and any(word in query_lower for word in ['delay', 'problem', 'performance']):
        return QueryIntent(query_type='sku_delay_analysis', filters={}, limit=10, confidence=0.95)
    
    # DELAYED SHIPMENTS - "delayed", "late", "which shipment"
    if any(phrase in query_lower for phrase in ['delayed shipment', 'late delivery', 'late deliveries', 'which shipment', 'show delayed', 'list delayed']):
        return QueryIntent(query_type='delayed_shipments', filters={}, limit=10, confidence=0.95)
    
    # ORDERS BY DESTINATION - "destination", "to which", "which destination", "more orders"
    if any(phrase in query_lower for phrase in ['destination', 'to which', 'shipments to', 'orders to', 'which destination have', 'more orders']):
        return QueryIntent(query_type='orders_by_destination', filters={}, limit=10, confidence=0.95)
    
    # ORDERS BY SOURCE - "source", "from which", "orders from"
    if any(phrase in query_lower for phrase in ['orders from', 'from which', 'source location', 'orders.*source']):
        return QueryIntent(query_type='orders_by_source', filters={}, limit=10, confidence=0.95)
    
    # SUMMARY STATS - "summary", "overview", "total shipments", "statistics"
    if any(phrase in query_lower for phrase in ['summary', 'overview', 'statistics', 'total shipment', 'current status', 'overall']):
        return QueryIntent(query_type='summary_stats', filters={}, confidence=0.85)
    
    # GENERATIVE INSIGHTS - "recommend", "suggest", "improve", "optimize"
    if any(phrase in query_lower for phrase in ['recommend', 'suggest', 'improve', 'optimize', 'strategy', 'best practice', 'insight', 'solution']):
        return QueryIntent(query_type='generative_insights', filters={}, confidence=0.75)
    
    # FALLBACK - return summary stats as default (not training mode)
    return QueryIntent(query_type='summary_stats', filters={}, confidence=0.5)

def extract_sku_code(query: str) -> Optional[str]:
    """Extract SKU code from query (e.g., SKU-0481)"""
    import re
    match = re.search(r'(sku[- ]?\d+)', query, re.IGNORECASE)
    if match:
        return match.group(1).replace(' ', '-')
    return None

def format_intent_for_summary(intent: QueryIntent) -> str:
    """Format intent for LLM summary"""
    filters_str = " with " + ", ".join(f"{k}={v}" for k, v in intent.filters.items()) if intent.filters else ""
    return f"Query: {intent.query_type}{filters_str}"
