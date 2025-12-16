"""
IMPROVED SUPPLY CHAIN QUERY ANALYZER
Accurate metrics calculation and intelligent response generation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List, Any


class ImprovedQueryAnalyzer:
    """Accurate supply chain metrics analyzer"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare and clean data for analysis"""
        # Convert date columns
        date_cols = ['departed_at', 'expected_arrival', 'arrived_at']
        for col in date_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
    
    # ========== CORE METRICS ==========
    
    def get_on_time_rate(self) -> Dict[str, Any]:
        """Calculate accurate on-time delivery rate"""
        
        # Only count arrived shipments for on-time calculation
        arrived = self.df[self.df['status'] == 'ARRIVED'].copy()
        
        if len(arrived) == 0:
            return {
                'on_time_rate': 0.0,
                'on_time_count': 0,
                'total_arrived': 0,
                'late_count': 0,
                'late_days_avg': 0,
                'status_breakdown': {
                    'arrived': 0,
                    'in_transit': 0
                }
            }
        
        # Calculate on-time (arrived_at <= expected_arrival)
        arrived['is_on_time'] = arrived['arrived_at'] <= arrived['expected_arrival']
        on_time_count = arrived['is_on_time'].sum()
        on_time_rate = (on_time_count / len(arrived) * 100) if len(arrived) > 0 else 0
        
        # Calculate average delay for late shipments
        late = arrived[~arrived['is_on_time']].copy()
        if len(late) > 0:
            late['delay_days'] = (late['arrived_at'] - late['expected_arrival']).dt.days
            late_days_avg = late['delay_days'].mean()
        else:
            late_days_avg = 0
        
        return {
            'on_time_rate': round(on_time_rate, 1),
            'on_time_count': int(on_time_count),
            'total_arrived': int(len(arrived)),
            'late_count': int(len(late)),
            'late_days_avg': round(late_days_avg, 1),
            'status_breakdown': {
                'arrived': int(len(self.df[self.df['status'] == 'ARRIVED'])),
                'in_transit': int(len(self.df[self.df['status'] == 'IN_TRANSIT']))
            }
        }
    
    def get_sku_count(self) -> Dict[str, Any]:
        """Get exact unique SKU count"""
        total_skus = self.df['sku'].nunique()
        
        # Get SKU volume distribution
        sku_volume = self.df.groupby('sku').agg({
            'quantity': 'sum',
            'shipment_id': 'count'
        }).reset_index()
        sku_volume.columns = ['sku', 'total_units', 'shipment_count']
        sku_volume = sku_volume.sort_values('total_units', ascending=False)
        
        return {
            'total_skus': int(total_skus),
            'total_units': int(self.df['quantity'].sum()),
            'avg_units_per_sku': round(self.df['quantity'].sum() / total_skus, 0),
            'top_5_skus': sku_volume.head(5).to_dict('records')
        }
    
    def get_location_analysis(self) -> Dict[str, Any]:
        """Analyze source and destination locations"""
        sources = self.df['source_location'].nunique()
        destinations = self.df['destination_location'].nunique()
        unique_routes = self.df.groupby(['source_location', 'destination_location']).size()
        
        return {
            'unique_source_locations': int(sources),
            'unique_destination_locations': int(destinations),
            'unique_routes': int(len(unique_routes)),
            'total_route_combinations_possible': sources * destinations,
        }
    
    def get_all_destination_metrics(self) -> Dict[str, Any]:
        """Get shipment counts and metrics for ALL destination locations"""
        dest_breakdown = self.df.groupby('destination_location').agg({
            'shipment_id': 'count',
            'quantity': 'sum'
        }).reset_index()
        dest_breakdown.columns = ['location', 'shipment_count', 'total_units']
        dest_breakdown = dest_breakdown.sort_values('shipment_count', ascending=False)
        
        # Add on-time rate for each location
        metrics = []
        for _, row in dest_breakdown.iterrows():
            loc = row['location']
            loc_data = self.get_shipments_by_location(loc, is_source=False)
            metrics.append({
                'location': loc,
                'shipment_count': int(row['shipment_count']),
                'total_units': int(row['total_units']),
                'on_time_rate': loc_data.get('on_time_rate', 0),
                'status_breakdown': loc_data.get('status_breakdown', {})
            })
        
        return {
            'total_destination_locations': len(metrics),
            'destinations': metrics
        }
    
    def get_shipment_details(self, shipment_id: str) -> Dict[str, Any]:
        """Get detailed info for a specific shipment"""
        shp = self.df[self.df['shipment_id'].str.upper() == shipment_id.upper()]
        
        if len(shp) == 0:
            return {'error': f'Shipment {shipment_id} not found'}
        
        shp = shp.iloc[0]
        
        # Calculate delay
        if pd.notna(shp['arrived_at']):
            delay_days = (shp['arrived_at'] - shp['expected_arrival']).days
            status_display = f"Delivered {'On-Time' if delay_days <= 0 else f'Late (by {abs(delay_days)} days)'}"
        else:
            delay_days = (pd.Timestamp.now() - shp['expected_arrival']).days if shp['status'] == 'IN_TRANSIT' else 0
            status_display = shp['status']
        
        return {
            'shipment_id': shp['shipment_id'],
            'sku': shp['sku'],
            'quantity': int(shp['quantity']),
            'source': shp['source_location'],
            'destination': shp['destination_location'],
            'departed': str(shp['departed_at']),
            'expected_arrival': str(shp['expected_arrival']),
            'actual_arrival': str(shp['arrived_at']) if pd.notna(shp['arrived_at']) else 'N/A',
            'status': shp['status'],
            'delay_days': int(delay_days),
            'risk_level': self._calculate_risk(shp),
            'formatted_response': self._format_shipment_card(shp)
        }
    
    def get_shipments_by_location(self, location: str, is_source: bool = True) -> Dict[str, Any]:
        """Get shipments from/to a location"""
        if is_source:
            filtered = self.df[self.df['source_location'].str.contains(location, case=False, na=False)]
            loc_type = 'source'
        else:
            filtered = self.df[self.df['destination_location'].str.contains(location, case=False, na=False)]
            loc_type = 'destination'
        
        if len(filtered) == 0:
            return {
                'location': location,
                'type': loc_type,
                'shipment_count': 0,
                'error': f'No shipments found from/to {location}'
            }
        
        # Status breakdown
        status_counts = filtered['status'].value_counts().to_dict()
        
        # On-time rate for arrived shipments
        arrived = filtered[filtered['status'] == 'ARRIVED']
        if len(arrived) > 0:
            on_time = (arrived['arrived_at'] <= arrived['expected_arrival']).sum()
            on_time_rate = round(on_time / len(arrived) * 100, 1)
        else:
            on_time_rate = 0.0
        
        return {
            'location': location,
            'type': loc_type,
            'shipment_count': int(len(filtered)),
            'total_units': int(filtered['quantity'].sum()),
            'on_time_rate': on_time_rate,
            'status_breakdown': status_counts,
            'unique_skus': int(filtered['sku'].nunique()),
            'unique_routes': int(filtered.groupby(['source_location', 'destination_location']).ngroups)
        }
    
    def get_route_performance(self, source: str = None, dest: str = None, limit: int = 10) -> Dict[str, Any]:
        """Analyze route performance"""
        routes = self.df.groupby(['source_location', 'destination_location']).agg({
            'shipment_id': 'count',
            'quantity': 'sum',
            'status': lambda x: (x == 'ARRIVED').sum()
        }).reset_index()
        
        routes.columns = ['source', 'destination', 'shipment_count', 'total_units', 'arrived_count']
        
        # Filter by source/dest if provided
        if source:
            routes = routes[routes['source'].str.contains(source, case=False, na=False)]
        if dest:
            routes = routes[routes['destination'].str.contains(dest, case=False, na=False)]
        
        # Calculate on-time rate
        routes['on_time_rate'] = routes.apply(
            lambda row: self._calculate_route_on_time(row['source'], row['destination']),
            axis=1
        )
        
        routes = routes.sort_values('on_time_rate', ascending=False).head(limit)
        
        return {
            'total_routes_analyzed': int(len(routes)),
            'top_routes': routes[['source', 'destination', 'shipment_count', 'on_time_rate']].to_dict('records'),
            'best_route': routes.iloc[0].to_dict() if len(routes) > 0 else None,
            'worst_route': routes.iloc[-1].to_dict() if len(routes) > 0 else None
        }
    
    def get_risk_shipments(self, limit: int = 10) -> Dict[str, Any]:
        """Identify high-risk shipments"""
        risk_df = self.df[self.df['status'] == 'IN_TRANSIT'].copy()
        risk_df['days_overdue'] = (pd.Timestamp.now() - risk_df['expected_arrival']).dt.days
        risk_df = risk_df[risk_df['days_overdue'] > 0]
        
        if len(risk_df) == 0:
            return {'risk_shipments': [], 'critical_count': 0}
        
        risk_df = risk_df.sort_values('days_overdue', ascending=False).head(limit)
        
        critical = len(risk_df[risk_df['days_overdue'] >= 5])
        
        return {
            'critical_shipments': critical,
            'total_at_risk': int(len(self.df[self.df['status'] == 'IN_TRANSIT'])),
            'risk_list': risk_df[['shipment_id', 'sku', 'quantity', 'source_location', 'destination_location', 'days_overdue']].to_dict('records'),
            'sample_risks': risk_df.head(3)[['shipment_id', 'source_location', 'destination_location']].to_dict('records')
        }
    
    # ========== HELPER METHODS ==========
    
    def _calculate_risk(self, shipment: pd.Series) -> str:
        """Determine risk level"""
        if shipment['status'] == 'ARRIVED':
            if pd.notna(shipment['arrived_at']):
                delay = (shipment['arrived_at'] - shipment['expected_arrival']).days
                if delay > 10:
                    return 'HIGH'
                elif delay > 5:
                    return 'MEDIUM'
                else:
                    return 'LOW'
        elif shipment['status'] == 'IN_TRANSIT':
            days_overdue = (pd.Timestamp.now() - shipment['expected_arrival']).days
            if days_overdue >= 5:
                return 'HIGH'
            elif days_overdue >= 2:
                return 'MEDIUM'
        return 'LOW'
    
    def _calculate_route_on_time(self, source: str, destination: str) -> float:
        """Calculate on-time rate for specific route"""
        route = self.df[(self.df['source_location'] == source) & (self.df['destination_location'] == destination)]
        arrived = route[route['status'] == 'ARRIVED']
        
        if len(arrived) == 0:
            return 0.0
        
        on_time = (arrived['arrived_at'] <= arrived['expected_arrival']).sum()
        return round(on_time / len(arrived) * 100, 1)
    
    def _format_shipment_card(self, shp: pd.Series) -> str:
        """Format shipment as readable card"""
        risk = self._calculate_risk(shp)
        risk_icon = '[HIGH]' if risk == 'HIGH' else '[MED]' if risk == 'MEDIUM' else '[LOW]'
        
        if pd.notna(shp['arrived_at']):
            delay = (shp['arrived_at'] - shp['expected_arrival']).days
            status_str = f"Delivered {'On-Time' if delay <= 0 else f'Late ({abs(delay)} days)'}"
        else:
            status_str = shp['status']
        
        return (
            f"{risk_icon} {shp['shipment_id']} | {shp['sku']} ({int(shp['quantity'])} units) | "
            f"{shp['source_location']}→{shp['destination_location']} | {status_str}"
        )


def analyze_query(df: pd.DataFrame, query_type: str, **params) -> Dict[str, Any]:
    """Main query analyzer function"""
    analyzer = ImprovedQueryAnalyzer(df)
    
    if query_type == 'on_time_rate':
        return analyzer.get_on_time_rate()
    elif query_type == 'sku_count':
        return analyzer.get_sku_count()
    elif query_type == 'locations':
        return analyzer.get_location_analysis()
    elif query_type == 'shipment_details':
        return analyzer.get_shipment_details(params.get('shipment_id', ''))
    elif query_type == 'location_shipments':
        return analyzer.get_shipments_by_location(
            params.get('location', ''),
            params.get('is_source', True)
        )
    elif query_type == 'route_performance':
        return analyzer.get_route_performance(
            params.get('source'),
            params.get('dest'),
            params.get('limit', 10)
        )
    elif query_type == 'risk_shipments':
        return analyzer.get_risk_shipments(params.get('limit', 10))
    else:
        return {'error': f'Unknown query type: {query_type}'}


if __name__ == "__main__":
    print("[OK] Improved Query Analyzer Ready")
    print("   Supports: on_time_rate, sku_count, locations, shipment_details, location_shipments, route_performance, risk_shipments")
