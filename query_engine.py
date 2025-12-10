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
    """Find CSV file in the same directory as this script"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # CSV file names to search for
    csv_filenames = ['shipment_data_1M.csv', 'shipment_data.csv']
    
    for filename in csv_filenames:
        csv_path = os.path.join(script_dir, filename)
        if os.path.exists(csv_path):
            print(f"[OK] Found CSV at: {csv_path}")
            return csv_path
    
    print(f"[ERROR] CSV not found in {script_dir}. Looked for: {csv_filenames}")
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
        print(f"[OK] Loaded {len(_csv_data)} records from {csv_path}")
        print(f"Columns: {_csv_data.columns.tolist()}")
        return _csv_data
    except Exception as e:
        print(f"[ERROR] Error loading CSV: {e}")
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
        df['route'] = df['source_location'] + ' -> ' + df['destination_location']
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
        
        # Normalize status to uppercase and strip whitespace
        df['status_norm'] = df['status'].astype(str).str.strip().str.upper()
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        
        # A shipment is delayed if:
        # 1. Status is explicitly DELAYED/LATE, OR
        # 2. arrived_at > expected_arrival (for arrived shipments)
        df['is_delayed'] = (df['status_norm'].isin(['DELAYED', 'LATE'])) | \
                           ((df['arrived_at'] > df['expected_arrival']) & (df['arrived_at'].notna()))
        
        # Group by SKU and calculate delay rate across ALL shipments
        sku_delay_rate = df.groupby('sku').agg({
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
        
        # Normalize status to uppercase and strip whitespace
        df['status_norm'] = df['status'].astype(str).str.strip().str.upper()
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        df['route'] = df['source_location'] + ' -> ' + df['destination_location']
        
        # A shipment is delayed if:
        # 1. Status is explicitly DELAYED/LATE, OR
        # 2. arrived_at > expected_arrival (for arrived shipments)
        df['is_delayed'] = (df['status_norm'].isin(['DELAYED', 'LATE'])) | \
                           ((df['arrived_at'] > df['expected_arrival']) & (df['arrived_at'].notna()))
        
        # Group by route and calculate delay rate across ALL shipments
        route_delay_rate = df.groupby('route').agg({
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

def get_orders_by_destination(limit: int = 10, **kwargs) -> QueryResult:
    """Get shipment count by destination location"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='orders_by_destination',
                error="No data available",
                summary="No data available"
            )
        
        dest_counts = df.groupby('destination_location').size().reset_index(name='shipment_count')
        dest_counts = dest_counts.sort_values('shipment_count', ascending=False)
        
        top_destinations = dest_counts.head(limit).to_dict('records')
        
        return QueryResult(
            query_type='orders_by_destination',
            result={'total_destinations': len(dest_counts)},
            data=top_destinations,
            summary=f"Top {limit} destinations by shipment count"
        )
    except Exception as e:
        return QueryResult(
            query_type='orders_by_destination',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_orders_by_source(limit: int = 10, **kwargs) -> QueryResult:
    """Get shipment count by source location"""
    try:
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='orders_by_source',
                error="No data available",
                summary="No data available"
            )
        
        source_counts = df.groupby('source_location').size().reset_index(name='shipment_count')
        source_counts = source_counts.sort_values('shipment_count', ascending=False)
        
        top_sources = source_counts.head(limit).to_dict('records')
        
        return QueryResult(
            query_type='orders_by_source',
            result={'total_sources': len(source_counts)},
            data=top_sources,
            summary=f"Top {limit} source locations by shipment count"
        )
    except Exception as e:
        return QueryResult(
            query_type='orders_by_source',
            error=str(e),
            summary=f"Error: {str(e)}"
        )

def get_generative_insights(limit: int = 10, **kwargs) -> QueryResult:
    """Generate insights and recommendations from supply chain data"""
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
        in_transit = len(df[df['status'] == 'IN_TRANSIT'])
        
        df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], errors='coerce')
        df['arrived_at'] = pd.to_datetime(df['arrived_at'], errors='coerce')
        
        delayed = len(df[(df['arrived_at'] > df['expected_arrival']) & (df['arrived_at'].notna())])
        on_time = arrived - delayed
        delay_rate = (delayed / total * 100) if total > 0 else 0
        on_time_rate = (on_time / total * 100) if total > 0 else 0
        
        # Get top problematic routes
        df['route'] = df['source_location'] + ' -> ' + df['destination_location']
        route_data = df[df['arrived_at'].notna()].groupby('route').agg({
            'shipment_id': 'count',
            'arrived_at': lambda x: (x > df.loc[x.index, 'expected_arrival']).sum()
        }).reset_index()
        route_data.columns = ['route', 'total', 'delayed']
        route_data['delay_rate'] = (route_data['delayed'] / route_data['total'] * 100)
        top_problem_routes = route_data.nlargest(3, 'delay_rate')
        
        # Get SKU insights
        sku_data = df.groupby('sku').agg({
            'shipment_id': 'count',
            'quantity': 'sum'
        }).reset_index()
        sku_data.columns = ['sku', 'shipments', 'total_quantity']
        sku_data = sku_data.sort_values('shipments', ascending=False).head(3)
        
        summary = f"""## 📊 Supply Chain Analytics Report

**Overall Performance:**
• Total Shipments: {total:,}
• On-Time Deliveries: {on_time:,} ({on_time_rate:.1f}%)
• Delayed Deliveries: {delayed:,} ({delay_rate:.1f}%)
• In Transit: {in_transit:,}
• Unique SKUs: {df['sku'].nunique()}
• Unique Routes: {df['route'].nunique()}

**Top Problem Routes (by delay rate):**"""
        
        for idx, row in top_problem_routes.iterrows():
            summary += f"\n• {row['route']}: {row['delay_rate']:.1f}% delays ({int(row['delayed'])}/{int(row['total'])} shipments)"
        
        summary += f"\n\n**Top SKUs by Volume:**"
        for idx, row in sku_data.iterrows():
            summary += f"\n• {row['sku']}: {int(row['shipments'])} shipments ({int(row['total_quantity'])} units)"
        
        summary += f"""\n\n**Key Recommendations:**
1. 🎯 Focus on reducing delay rate from {delay_rate:.1f}% to below 20%
2. 🚚 Optimize top problem routes for faster transit
3. 📦 Implement quality checks for high-volume SKUs
4. ⚠️ Set up predictive alerts for delay-prone routes
5. 📊 Monitor destination and source patterns for efficiency"""
        
        return QueryResult(
            query_type='generative_insights',
            result={
                'total_shipments': total,
                'on_time_rate': round(on_time_rate, 2),
                'delay_rate': round(delay_rate, 2),
                'unique_skus': df['sku'].nunique(),
                'unique_routes': df['route'].nunique()
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

def get_training_mode(limit: int = 10, **kwargs) -> QueryResult:
    """Handle queries in training mode - show we're working on it"""
    return QueryResult(
        query_type='training_mode',
        result={},
        data=[],
        summary="""🚀 **Advanced Query in Training Mode**

We're actively enhancing our AI to understand this query better! Our model is being trained on similar questions to provide more accurate results.

**What we currently support:**
• ✅ SKU analysis (count, delays, orders per SKU)
• ✅ Route performance (delays, top routes)
• ✅ Shipment status (delayed, in transit, arrived)
• ✅ Location analysis (destinations, sources)
• ✅ Supply chain overview & metrics

**Coming Soon:**
• 📚 Advanced natural language understanding
• 🔮 Predictive analytics for ETAs
• 🎯 Custom filters and drilling down
• 📊 Time-series forecasting
• 🤖 Generative insights & recommendations

**Try asking:**
- "Which routes have most delays?"
- "Show problematic SKUs"
- "Orders by destination"
- "How many SKUs do we have?"
- "Total shipments"
"""
    )

def get_shipment_details(shipment_id: str, **kwargs) -> QueryResult:
    """Get details for a specific shipment using enrichment layer"""
    try:
        from data_enrichment import enrich_shipment
        
        df = load_csv()
        if df.empty:
            return QueryResult(
                query_type='shipment_details',
                error="No data available",
                summary="No data available"
            )
        
        # Normalize shipment_id for case-insensitive matching
        normalized_id = shipment_id.strip().upper()
        
        # Try to find the shipment (handle both case-sensitive and case-insensitive)
        shipment = df[df['shipment_id'].astype(str).str.strip().str.upper() == normalized_id]
        
        if shipment.empty:
            return QueryResult(
                query_type='shipment_details',
                error=f"Shipment {shipment_id} not found",
                summary=f"No shipment found with ID: {shipment_id}"
            )
        
        # Use enrichment layer to transform raw data
        enriched = enrich_shipment(shipment.iloc[0].to_dict())
        
        # Return as structured JSON (NOT raw CSV)
        return QueryResult(
            query_type='shipment_details',
            result={
                'shipment_id': enriched.shipment_id,
                'sku': enriched.sku,
                'quantity': enriched.quantity,
                'status': enriched.status_label,
                'health': enriched.shipment_health,
                'risk_score': enriched.risk_score,
            },
            data=[{
                'shipment_id': enriched.shipment_id,
                'sku': enriched.sku,
                'quantity': enriched.quantity,
                'route': enriched.route,
                'status': enriched.status_label,
                'status_interpretation': enriched.status_interpretation,
                'shipped_date': enriched.shipped_date,
                'expected_arrival': enriched.expected_arrival,
                'actual_arrival': enriched.actual_arrival,
                'transit_days': enriched.transit_days,
                'delay_days': enriched.delay_days,
                'health': enriched.shipment_health,
                'risk_score': enriched.risk_score,
                'timeline_summary': enriched.timeline_summary,
                'eta_forecast': enriched.eta_forecast,
                'recommendations': enriched.recommendations,
            }],
            summary=f"Shipment {enriched.shipment_id}: {enriched.status_label}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return QueryResult(
            query_type='shipment_details',
            error=str(e),
            summary=f"Error retrieving shipment details: {str(e)}"
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
    'orders_by_destination': get_orders_by_destination,
    'orders_by_source': get_orders_by_source,
    'generative_insights': get_generative_insights,
    'shipment_details': get_shipment_details,
    'training_mode': get_training_mode
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
