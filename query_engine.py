"""
Analytics Query Engine - Structured data extraction from CSV
"""
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class QueryResult:
    """Structured result format"""
    query_type: str
    result: Dict[str, Any] = None
    data: List[Dict[str, Any]] = None
    summary: str = ""
    error: str = None

# Global data cache
_csv_data = None

def find_csv():
    """Find CSV file in multiple locations"""
    possible_paths = [
        'shipment_data_1M.csv',
        'shipment_data.csv',
        './shipment_data_1M.csv',
        './shipment_data.csv',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found CSV at: {path}")
            return path
    
    print(f"❌ CSV not found. Tried: {possible_paths}")
    return None

def load_csv() -> pd.DataFrame:
    """Load CSV once and cache it"""
    global _csv_data
    
    if _csv_data is not None:
        return _csv_data
    
    csv_path = find_csv()
    if not csv_path:
        return pd.DataFrame()
    
    try:
        _csv_data = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(_csv_data)} records from {csv_path}")
        print(f"Columns: {_csv_data.columns.tolist()}")
        return _csv_data
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()

def get_sku_count(limit: int = 10, **kwargs) -> QueryResult:
    """Get total number of unique SKUs"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='sku_count',
                error="No data available",
                summary="No data available"
            )
        
        total = df['sku'].nunique()
        
        return QueryResult(
            query_type='sku_count',
            result={'total_skus': int(total)},
            data=[],
            summary=f"Total unique SKUs: {total}"
        )
    except Exception as e:
        return QueryResult(
            query_type='sku_count',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_orders_per_sku(limit: int = 10, **kwargs) -> QueryResult:
    """Get order count grouped by SKU"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='orders_per_sku',
                error="No data available",
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
            summary=f"Top {limit} SKUs by order count"
        )
    except Exception as e:
        return QueryResult(
            query_type='orders_per_sku',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_top_routes(limit: int = 10, **kwargs) -> QueryResult:
    """Get top routes by shipment count"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='top_routes',
                error="No data available",
                summary="No data available"
            )
        
        # Create route column
        df['route'] = df['source_location'] + ' → ' + df['destination_location']
        route_counts = df.groupby('route').size().reset_index(name='shipment_count')
        route_counts = route_counts.sort_values('shipment_count', ascending=False)
        
        top_routes_data = route_counts.head(limit).to_dict('records')
        
        return QueryResult(
            query_type='top_routes',
            result={'total_routes': len(route_counts)},
            data=top_routes_data,
            summary=f"Top {limit} routes by shipment count"
        )
    except Exception as e:
        return QueryResult(
            query_type='top_routes',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_delayed_shipments(limit: int = 10, **kwargs) -> QueryResult:
    """Get delayed shipments"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='delayed_shipments',
                error="No data available",
                summary="No data available"
            )
        
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        
        arrived = df[df['status'] == 'ARRIVED'].copy()
        arrived.loc[:, 'delay_days'] = (arrived['arrived_at'] - arrived['expected_arrival']).dt.days
        
        delayed = arrived[arrived['delay_days'] > 0].nlargest(limit, 'delay_days')
        
        delayed_data = delayed[['shipment_id', 'sku', 'status', 'delay_days']].to_dict('records')
        
        return QueryResult(
            query_type='delayed_shipments',
            result={'total_delayed': len(delayed)},
            data=delayed_data,
            summary=f"Found {len(delayed)} delayed shipments"
        )
    except Exception as e:
        return QueryResult(
            query_type='delayed_shipments',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_summary_stats(limit: int = 10, **kwargs) -> QueryResult:
    """Get overall summary statistics"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='summary_stats',
                error="No data available",
                summary="No data available"
            )
        
        total_shipments = len(df)
        arrived_count = len(df[df['status'] == 'ARRIVED'])
        in_transit_count = len(df[df['status'] == 'IN_TRANSIT'])
        delayed_count = len(df[df['status'] == 'DELAYED'])
        
        on_time_rate = (arrived_count / total_shipments * 100) if total_shipments > 0 else 0
        delay_rate = 100 - on_time_rate
        
        unique_skus = df['sku'].nunique()
        
        # Try to get routes
        try:
            df['route'] = df['source_location'] + ' → ' + df['destination_location']
            unique_routes = df['route'].nunique()
        except:
            unique_routes = 0
        
        return QueryResult(
            query_type='summary_stats',
            result={
                'total_shipments': total_shipments,
                'arrived_count': arrived_count,
                'in_transit_count': in_transit_count,
                'delayed_count': delayed_count,
                'on_time_rate_pct': round(on_time_rate, 2),
                'delay_rate_pct': round(delay_rate, 2),
                'unique_skus': unique_skus,
                'unique_routes': unique_routes
            },
            data=[],
            summary=f"Supply chain overview - {total_shipments} total shipments"
        )
    except Exception as e:
        return QueryResult(
            query_type='summary_stats',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_sku_delay_analysis(limit: int = 10, **kwargs) -> QueryResult:
    """Analyze SKUs by delay rate"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='sku_delay_analysis',
                error="No data available",
                summary="No data available"
            )
        
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        
        arrived = df[df['status'] == 'ARRIVED'].copy()
        arrived.loc[:, 'is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
        
        sku_delay_rate = arrived.groupby('sku').agg({
            'is_delayed': lambda x: (x.sum() / len(x) * 100),
            'shipment_id': 'count'
        }).reset_index()
        sku_delay_rate.columns = ['sku', 'delay_rate_pct', 'shipment_count']
        sku_delay_rate = sku_delay_rate.sort_values('delay_rate_pct', ascending=False)
        
        top_skus = sku_delay_rate.head(limit).to_dict('records')
        
        return QueryResult(
            query_type='sku_delay_analysis',
            result={'total_skus_analyzed': len(sku_delay_rate)},
            data=top_skus,
            summary=f"Top {limit} SKUs by delay rate"
        )
    except Exception as e:
        return QueryResult(
            query_type='sku_delay_analysis',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_route_delay_analysis(limit: int = 10, **kwargs) -> QueryResult:
    """Analyze routes by delay rate"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='route_delay_analysis',
                error="No data available",
                summary="No data available"
            )
        
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        df['route'] = df['source_location'] + ' → ' + df['destination_location']
        
        arrived = df[df['status'] == 'ARRIVED'].copy()
        arrived.loc[:, 'is_delayed'] = arrived['arrived_at'] > arrived['expected_arrival']
        
        route_delay_rate = arrived.groupby('route').agg({
            'is_delayed': lambda x: (x.sum() / len(x) * 100),
            'shipment_id': 'count'
        }).reset_index()
        route_delay_rate.columns = ['route', 'delay_rate_pct', 'shipment_count']
        route_delay_rate = route_delay_rate.sort_values('delay_rate_pct', ascending=False)
        
        top_routes_data = route_delay_rate.head(limit).to_dict('records')
        
        return QueryResult(
            query_type='route_delay_analysis',
            result={'total_routes_analyzed': len(route_delay_rate)},
            data=top_routes_data,
            summary=f"Top {limit} routes by delay rate"
        )
    except Exception as e:
        return QueryResult(
            query_type='route_delay_analysis',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_generative_insights(limit: int = 10, **kwargs) -> QueryResult:
    """Generate insights and recommendations"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='generative_insights',
                error="No data available",
                summary="No data available"
            )
        
        # Get summary metrics
        total = len(df)
        arrived = len(df[df['status'] == 'ARRIVED'])
        delayed = len(df[df['status'] == 'DELAYED'])
        delay_rate = (delayed / total * 100) if total > 0 else 0
        
        summary = f"""## 📊 Supply Chain Insights

**Performance Metrics:**
- Total Shipments: {total:,}
- Arrived: {arrived:,}
- Delayed: {delayed:,}
- Delay Rate: {delay_rate:.2f}%

**Key Recommendations:**
1. Focus on reducing delay rate by {min(delay_rate, 30):.1f} percentage points
2. Investigate top problematic SKUs and routes
3. Optimize shipping logistics for delayed routes
4. Implement real-time tracking for high-risk shipments
5. Set up predictive alerts for potential delays"""
        
        return QueryResult(
            query_type='generative_insights',
            result={
                'total_shipments': total,
                'delay_rate': round(delay_rate, 2)
            },
            data=[],
            summary=summary
        )
    except Exception as e:
        return QueryResult(
            query_type='generative_insights',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

# Query dispatcher
QUERY_HANDLERS = {
    'sku_count': get_sku_count,
    'orders_per_sku': get_orders_per_sku,
    'top_routes': get_top_routes,
    'delayed_shipments': get_delayed_shipments,
    'sku_delay_analysis': get_sku_delay_analysis,
    'route_delay_analysis': get_route_delay_analysis,
    'summary_stats': get_summary_stats,
    'generative_insights': get_generative_insights
}

def execute_query(query_type: str, **kwargs) -> QueryResult:
    """Execute a structured query"""
    handler = QUERY_HANDLERS.get(query_type)
    
    if not handler:
        return QueryResult(
            query_type=query_type,
            error=f"Unknown query type: {query_type}",
            summary=f"Unknown query type: {query_type}"
        )
    
    try:
        return handler(**kwargs)
    except Exception as e:
        return QueryResult(
            query_type=query_type,
            error=str(e),
            summary=f"Error: {str(e)}"
        )
