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
    
    # Orders by destination location
    if any(phrase in query_lower for phrase in ['destination order', 'order to ', 'how many.*destination', 'shipment.*to ', 'orders.*destination', 'destination shipment', 'to which', 'orders towards']):
        return QueryIntent(
            query_type='orders_by_destination',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # Orders by source location
    if any(phrase in query_lower for phrase in ['source order', 'order from ', 'how many.*source', 'shipment.*from ', 'orders.*source', 'source shipment', 'from which', 'orders from source']):
        return QueryIntent(
            query_type='orders_by_source',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # Orders per SKU (check early - higher priority)
    if any(phrase in query_lower for phrase in ['orders per sku', 'order count by sku', 'shipments per sku', 'which sku have more order', 'sku have more order', 'sku with more order', 'orders by sku', 'order per sku', 'which sku have more shipment', 'sku have more shipment', 'sku with more shipment', 'shipments by sku', 'shipment per sku', 'how many orders.*sku']):
        return QueryIntent(
            query_type='orders_per_sku',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # SKU count queries
    if any(phrase in query_lower for phrase in ['how many sku', 'total sku', 'sku count', 'number of sku', 'unique sku', 'how many different sku', 'total number of sku']):
        return QueryIntent(
            query_type='sku_count',
            filters={},
            confidence=0.95
        )
    
    # Top routes
    if any(phrase in query_lower for phrase in ['top route', 'busiest route', 'most shipment', 'popular route', 'highest shipment', 'most popular route', 'peak route', 'main route', 'how many route', 'how many different route', 'total route', 'number of route', 'unique route']):
        return QueryIntent(
            query_type='top_routes',
            filters={},
            limit=10,
            confidence=0.9
        )
    
    # Delayed shipments (check before SKU delay to avoid conflicts)
    if any(phrase in query_lower for phrase in ['delayed shipment', 'late shipment', 'delayed delivery', 'late delivery', 'show delayed', 'list delayed', 'which shipment delayed', 'delayed order', 'delayed orders']):
        return QueryIntent(
            query_type='delayed_shipments',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # SKU delay analysis (check before generic what/how)
    if any(phrase in query_lower for phrase in ['sku delay', 'problematic sku', 'sku by delay', 'sku performance', 'delay by sku', 'sku with delay', 'sku delay rate', 'delayed sku', 'which sku.*problem', 'which sku.*delay', 'sku.*most delay', 'sku.*problematic']):
        return QueryIntent(
            query_type='sku_delay_analysis',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # Route delay analysis (check before generic what/how)
    if any(phrase in query_lower for phrase in ['route delay', 'route performance', 'route by delay', 'problematic route', 'delay by route', 'route with delay', 'delayed route', 'route delay rate', 'which route.*delay', 'which route.*problem', 'route.*most delay', 'routes have.*most delay']):
        return QueryIntent(
            query_type='route_delay_analysis',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # Summary stats (check early - common queries)
    if any(phrase in query_lower for phrase in ['summary', 'overview', 'statistics', 'total shipments', 'all shipments', 'give me summary', 'overall', 'total order']):
        return QueryIntent(
            query_type='summary_stats',
            filters={},
            confidence=0.85
        )
    
    # Generative insights (open-ended supply chain questions)
    # IMPORTANT: Only match truly open-ended questions asking for recommendations/analysis
    # NOT queries asking for specific data (which should have matched above)
    if any(word in query_lower for word in ['recommend', 'suggest', 'improve', 'strategy', 'solution', 'optimize', 'best practice', 'efficiency', 'opportunity', 'insight', 'analysis', 'report']):
        return QueryIntent(
            query_type='generative_insights',
            filters={},
            confidence=0.75
        )
    
    # Default to summary stats if they ask generic "how" or "what" without specific keywords
    if any(word in query_lower for word in ['how', 'what', 'why']):
        return QueryIntent(
            query_type='summary_stats',
            filters={},
            confidence=0.65
        )

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
