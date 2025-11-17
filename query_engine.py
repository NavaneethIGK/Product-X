"""
Analytics Query Engine - Structured data extraction from CSV
Implements NLP → SQL-like queries → Data aggregation → Structured results
"""

import pandas as pd
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class QueryResult:
    """Structured result format"""
    query_type: str  # 'sku_count', 'orders_per_sku', 'top_routes', etc.
    result: Dict[str, Any]
    data: List[Dict[str, Any]]
    summary: str

# Global data cache
_csv_data = None
_skus = None
_routes = None

def load_csv(filepath: str = 'shipment_data_1M.csv') -> pd.DataFrame:
    """Load CSV once and cache it"""
    global _csv_data
    if _csv_data is None:
        try:
            _csv_data = pd.read_csv(filepath)
            print(f"Loaded {len(_csv_data)} shipment records")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return pd.DataFrame()
    return _csv_data

def get_sku_count(limit: int = 10, **kwargs) -> QueryResult:
    """Get total number of unique SKUs"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='sku_count',
            result={'total': 0, 'unique_skus': []},
            data=[],
            summary="No data available"
        )
    
    unique_skus = df['sku'].unique().tolist()
    total = len(unique_skus)
    
    return QueryResult(
        query_type='sku_count',
        result={'total': total},
        data=[{'sku': sku} for sku in sorted(unique_skus)[:20]],
        summary=f"Total unique SKUs: {total}"
    )

def get_orders_per_sku(limit: int = 10, **kwargs) -> QueryResult:
    """Get order count grouped by SKU"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='orders_per_sku',
            result={},
            data=[],
            summary="No data available"
        )
    
    sku_counts = df.groupby('sku').size().reset_index(name='order_count')
    sku_counts = sku_counts.sort_values('order_count', ascending=False)
    
    top_skus = sku_counts.head(limit).to_dict('records')
    total_orders = len(df)
    
    return QueryResult(
        query_type='orders_per_sku',
        result={
            'total_orders': total_orders,
            'unique_skus': len(sku_counts),
            'avg_orders_per_sku': round(total_orders / len(sku_counts), 2)
        },
        data=top_skus,
        summary=f"Top {limit} SKUs by order count (Total: {total_orders} orders)"
    )

def get_top_routes(limit: int = 10, **kwargs) -> QueryResult:
    """Get top routes by shipment count"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='top_routes',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['route'] = df['source_location'] + ' → ' + df['destination_location']
    route_counts = df.groupby('route').size().reset_index(name='shipment_count')
    route_counts = route_counts.sort_values('shipment_count', ascending=False)
    
    top_routes = route_counts.head(limit).to_dict('records')
    
    return QueryResult(
        query_type='top_routes',
        result={
            'total_routes': len(route_counts),
            'total_shipments': len(df)
        },
        data=top_routes,
        summary=f"Top {limit} routes by shipment volume"
    )

def get_delayed_shipments(min_delay_days: int = 1, limit: int = 10, **kwargs) -> QueryResult:
    """Get delayed shipments with details"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='delayed_shipments',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
    df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
    
    # Filter arrived shipments
    arrived = df[df['status'] == 'ARRIVED'].copy()
    
    # Calculate delay
    arrived['delay_days'] = (arrived['arrived_at'] - arrived['expected_arrival']).dt.days
    delayed = arrived[arrived['delay_days'] >= min_delay_days].copy()
    
    top_delayed = delayed.nlargest(limit, 'delay_days')[
        ['shipment_id', 'source_location', 'destination_location', 'sku', 'delay_days', 'status']
    ].to_dict('records')
    
    total_delayed_count = len(delayed)
    avg_delay = delayed['delay_days'].mean() if len(delayed) > 0 else 0
    
    return QueryResult(
        query_type='delayed_shipments',
        result={
            'total_delayed': total_delayed_count,
            'avg_delay_days': round(avg_delay, 2),
            'delay_percentage': round((total_delayed_count / len(arrived) * 100), 2)
        },
        data=top_delayed,
        summary=f"Found {total_delayed_count} delayed shipments (Avg delay: {avg_delay:.2f} days)"
    )

def get_sku_delay_analysis(limit: int = 10, **kwargs) -> QueryResult:
    """Get SKUs with highest delay rates"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='sku_delay_analysis',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
    df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
    
    arrived = df[df['status'] == 'ARRIVED'].copy()
    arrived['is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
    
    sku_delay_rate = arrived.groupby('sku').agg({
        'is_delayed': lambda x: (x.sum() / len(x) * 100),
        'shipment_id': 'count'
    }).reset_index()
    sku_delay_rate.columns = ['sku', 'delay_rate_pct', 'shipment_count']
    sku_delay_rate = sku_delay_rate.sort_values('delay_rate_pct', ascending=False)
    
    top_problem_skus = sku_delay_rate.head(limit).to_dict('records')
    
    return QueryResult(
        query_type='sku_delay_analysis',
        result={
            'total_skus_analyzed': len(sku_delay_rate),
            'avg_delay_rate': round(sku_delay_rate['delay_rate_pct'].mean(), 2)
        },
        data=top_problem_skus,
        summary=f"Top {limit} SKUs by delay rate"
    )

def get_route_delay_analysis(limit: int = 10, **kwargs) -> QueryResult:
    """Get routes with highest delay rates"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='route_delay_analysis',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['route'] = df['source_location'] + ' → ' + df['destination_location']
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
    df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
    
    arrived = df[df['status'] == 'ARRIVED'].copy()
    arrived['is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
    
    route_delay_rate = arrived.groupby('route').agg({
        'is_delayed': lambda x: (x.sum() / len(x) * 100),
        'shipment_id': 'count'
    }).reset_index()
    route_delay_rate.columns = ['route', 'delay_rate_pct', 'shipment_count']
    route_delay_rate = route_delay_rate.sort_values('delay_rate_pct', ascending=False)
    
    top_problem_routes = route_delay_rate.head(limit).to_dict('records')
    
    return QueryResult(
        query_type='route_delay_analysis',
        result={
            'total_routes_analyzed': len(route_delay_rate),
            'avg_delay_rate': round(route_delay_rate['delay_rate_pct'].mean(), 2)
        },
        data=top_problem_routes,
        summary=f"Top {limit} routes by delay rate"
    )

def filter_shipments(
    sku: Optional[str] = None,
    route: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    **kwargs
) -> QueryResult:
    """Filter shipments by various criteria"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='filtered_shipments',
            result={},
            data=[],
            summary="No data available"
        )
    
    result_df = df.copy()
    filters_applied = []
    
    if sku:
        result_df = result_df[result_df['sku'].str.contains(sku, case=False, na=False)]
        filters_applied.append(f"SKU: {sku}")
    
    if route:
        result_df['route'] = result_df['source_location'] + ' → ' + result_df['destination_location']
        result_df = result_df[result_df['route'].str.contains(route, case=False, na=False)]
        filters_applied.append(f"Route: {route}")
    
    if status:
        result_df = result_df[result_df['status'].str.contains(status, case=False, na=False)]
        filters_applied.append(f"Status: {status}")
    
    count = len(result_df)
    filtered_data = result_df.head(limit)[
        ['shipment_id', 'sku', 'source_location', 'destination_location', 'status']
    ].to_dict('records')
    
    filter_text = ", ".join(filters_applied) if filters_applied else "all"
    
    return QueryResult(
        query_type='filtered_shipments',
        result={
            'total_matching': count,
            'filters': filters_applied
        },
        data=filtered_data,
        summary=f"Found {count} shipments matching: {filter_text}"
    )

def get_summary_stats() -> QueryResult:
    """Get overall supply chain summary statistics"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='summary_stats',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
    df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
    
    total_shipments = len(df)
    arrived = df[df['status'] == 'ARRIVED']
    in_transit = df[df['status'] == 'IN_TRANSIT']
    
    arrived['is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
    delayed = arrived[arrived['is_delayed']]
    
    on_time_rate = (len(arrived) - len(delayed)) / len(arrived) * 100 if len(arrived) > 0 else 0
    delay_rate = len(delayed) / len(arrived) * 100 if len(arrived) > 0 else 0
    
    result = {
        'total_shipments': total_shipments,
        'arrived_count': len(arrived),
        'in_transit_count': len(in_transit),
        'delayed_count': len(delayed),
        'on_time_rate_pct': round(on_time_rate, 2),
        'delay_rate_pct': round(delay_rate, 2),
        'unique_skus': df['sku'].nunique(),
        'unique_routes': (df['source_location'] + ' → ' + df['destination_location']).nunique()
    }
    
    return QueryResult(
        query_type='summary_stats',
        result=result,
        data=[result],
        summary="Supply chain overview"
    )

def get_generative_insights(**kwargs) -> QueryResult:
    """Generate insights and recommendations from data for open-ended questions"""
    df = load_csv()
    if df.empty:
        return QueryResult(
            query_type='generative_insights',
            result={},
            data=[],
            summary="No data available"
        )
    
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
    df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
    
    # Gather key insights
    total_shipments = len(df)
    arrived = df[df['status'] == 'ARRIVED']
    in_transit = df[df['status'] == 'IN_TRANSIT']
    
    arrived['is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
    delayed = arrived[arrived['is_delayed']]
    
    on_time_rate = (len(arrived) - len(delayed)) / len(arrived) * 100 if len(arrived) > 0 else 0
    delay_rate = len(delayed) / len(arrived) * 100 if len(arrived) > 0 else 0
    
    # Find problematic SKUs
    sku_delays = arrived.groupby('sku')['is_delayed'].apply(lambda x: (x.sum() / len(x) * 100)).reset_index()
    sku_delays.columns = ['sku', 'delay_rate']
    sku_delays = sku_delays.sort_values('delay_rate', ascending=False)
    top_problem_skus = sku_delays.head(3)['sku'].tolist()
    
    # Find problematic routes
    df['route'] = df['source_location'] + ' → ' + df['destination_location']
    route_delays = arrived.groupby('route')['is_delayed'].apply(lambda x: (x.sum() / len(x) * 100)).reset_index()
    route_delays.columns = ['route', 'delay_rate']
    route_delays = route_delays.sort_values('delay_rate', ascending=False)
    top_problem_routes = route_delays.head(3)['route'].tolist()
    
    # Generate insights text
    insights = f"""
## Key Insights & Recommendations

**Current Performance:**
- Total Shipments: {total_shipments:,}
- On-Time Rate: {on_time_rate:.1f}%
- Delay Rate: {delay_rate:.1f}%
- Arrived Shipments: {len(arrived):,}
- In-Transit: {len(in_transit):,}

**Top Issues:**
1. **Problematic SKUs:** {', '.join(top_problem_skus) if top_problem_skus else 'None identified'}
2. **Problematic Routes:** {', '.join(top_problem_routes[:2]) if top_problem_routes else 'None identified'}
3. **Delayed Shipments:** {len(delayed):,} shipments delayed

**Recommendations:**
- Focus on routes with highest delay rates: {top_problem_routes[0] if top_problem_routes else 'N/A'}
- Investigate SKU quality/origin issues: {top_problem_skus[0] if top_problem_skus else 'N/A'}
- Implement expedited shipping for high-value routes
- Monitor in-transit shipments ({len(in_transit):,}) for potential delays
"""
    
    return QueryResult(
        query_type='generative_insights',
        result={
            'on_time_rate': round(on_time_rate, 2),
            'delay_rate': round(delay_rate, 2),
            'delayed_count': len(delayed),
            'total_shipments': total_shipments
        },
        data=[],
        summary=insights
    )

# Query dispatcher
QUERY_HANDLERS = {
    'sku_count': get_sku_count,
    'orders_per_sku': get_orders_per_sku,
    'top_routes': get_top_routes,
    'delayed_shipments': get_delayed_shipments,
    'sku_delay_analysis': get_sku_delay_analysis,
    'route_delay_analysis': get_route_delay_analysis,
    'filtered_shipments': filter_shipments,
    'summary_stats': get_summary_stats,
    'generative_insights': get_generative_insights
}

def execute_query(query_type: str, **kwargs) -> QueryResult:
    """Execute a structured query"""
    handler = QUERY_HANDLERS.get(query_type)
    if not handler:
        return QueryResult(
            query_type=query_type,
            result={},
            data=[],
            summary=f"Unknown query type: {query_type}"
        )
    
    # Only pass limit for handlers that support it
    if query_type in ['summary_stats', 'generative_insights']:
        return handler()
    else:
        return handler(**kwargs)
