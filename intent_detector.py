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
    
    # Orders per SKU (check FIRST - higher priority)
    if any(phrase in query_lower for phrase in ['orders per sku', 'order count by sku', 'shipments per sku', 'which sku have more order', 'sku have more order', 'sku with more order', 'orders by sku', 'order per sku', 'which sku have more shipment', 'sku have more shipment', 'sku with more shipment', 'shipments by sku', 'shipment per sku']):
        return QueryIntent(
            query_type='orders_per_sku',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # SKU count queries
    if any(word in query_lower for word in ['how many sku', 'total sku', 'sku count', 'number of sku', 'unique sku']):
        return QueryIntent(
            query_type='sku_count',
            filters={},
            confidence=0.95
        )
    
    # Top routes
    if any(phrase in query_lower for phrase in ['top route', 'busiest route', 'most shipment', 'popular route', 'highest shipment', 'most popular route']):
        return QueryIntent(
            query_type='top_routes',
            filters={},
            limit=10,
            confidence=0.9
        )
    
    # Delayed shipments (check before SKU delay to avoid conflicts)
    if any(phrase in query_lower for phrase in ['delayed shipment', 'late shipment', 'delayed delivery', 'late delivery', 'show delayed', 'list delayed']):
        return QueryIntent(
            query_type='delayed_shipments',
            filters={},
            limit=10,
            confidence=0.95
        )
    
    # SKU delay analysis
    if any(phrase in query_lower for phrase in ['sku delay', 'problematic sku', 'sku by delay', 'sku performance', 'delay by sku', 'sku with delay']):
        return QueryIntent(
            query_type='sku_delay_analysis',
            filters={},
            limit=10,
            confidence=0.9
        )
    
    # Route delay analysis
    if any(phrase in query_lower for phrase in ['route delay', 'route performance', 'route by delay', 'problematic route', 'delay by route', 'route with delay']):
        return QueryIntent(
            query_type='route_delay_analysis',
            filters={},
            limit=10,
            confidence=0.9
        )
    
    # Filter by SKU
    if 'sku' in query_lower and any(word in query_lower for word in ['show', 'filter', 'get', 'list', 'find']):
        # Extract SKU code if present
        sku_code = extract_sku_code(query_lower)
        return QueryIntent(
            query_type='filtered_shipments',
            filters={'sku': sku_code} if sku_code else {},
            limit=10,
            confidence=0.85
        )
    
    # Summary stats (check LAST - lowest priority as catch-all)
    if any(phrase in query_lower for phrase in ['summary', 'overview', 'statistics', 'total shipments ', 'all shipments']):
        return QueryIntent(
            query_type='summary_stats',
            filters={},
            confidence=0.85
        )
    
    # Generative insights (open-ended questions)
    # These are questions asking for recommendations, strategies, improvements
    if any(word in query_lower for word in ['how', 'what', 'why', 'can we', 'should we', 'could we', 'recommend', 'suggest', 'improve', 'strategy', 'solution', 'optimize', 'reduce', 'increase', 'best practice']):
        return QueryIntent(
            query_type='generative_insights',
            filters={},
            confidence=0.75
        )
    
    # Default to generative insights for unknown questions
    return QueryIntent(
        query_type='generative_insights',
        filters={},
        confidence=0.2
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
