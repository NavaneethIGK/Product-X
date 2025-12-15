"""
IMPROVED LLM RESPONSE GENERATOR
Accurate, crisp responses with proper supply chain formatting
"""

from typing import Dict, Tuple, Any, List
import pandas as pd
from improved_query_analyzer import analyze_query, ImprovedQueryAnalyzer
import re


class ImprovedResponseGenerator:
    """Generate accurate supply chain responses"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.analyzer = ImprovedQueryAnalyzer(df)
    
    def generate_response(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze user query and generate accurate response
        Returns: (response_text, metadata)
        """
        
        query_lower = user_query.lower().strip()
        
        # ========== QUERY TYPE DETECTION ==========
        
        # ON-TIME RATE queries
        if any(phrase in query_lower for phrase in ['on.?time', 'delivery rate', 'performance', 'how many.*on.?time']):
            return self._respond_on_time_rate()
        
        # SKU COUNT queries
        if any(phrase in query_lower for phrase in ['how many sku', 'total sku', 'sku count', 'unique sku']):
            return self._respond_sku_count()
        
        # SHIPMENT DETAILS queries
        shp_match = re.search(r'(shp[- ]?\d+)', query_lower, re.IGNORECASE)
        if shp_match:
            shipment_id = shp_match.group(1).replace(' ', '-').upper()
            return self._respond_shipment_details(shipment_id)
        
        # LOCATION queries
        location_match = re.search(r'(uk-lon|us-nyc|us-lax|cn-sha|cn-she|in-del|in-mum|de-ber|fr-par|jp-tok|sg-sin|ae-dxb|br-sao|mx-mex|au-syd|ca-tor|nl-ams|it-mil|es-mad|kr-icn)', query_lower, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).upper()
            if any(phrase in query_lower for phrase in ['from', 'source', 'origin', 'shipped from']):
                return self._respond_location_shipments(location, is_source=True)
            elif any(phrase in query_lower for phrase in ['to', 'destination', 'shipped to']):
                return self._respond_location_shipments(location, is_source=False)
            else:
                # Default to source location
                return self._respond_location_shipments(location, is_source=True)
        
        # ROUTE PERFORMANCE queries
        if any(phrase in query_lower for phrase in ['best route', 'top route', 'route perform', 'corridor']):
            return self._respond_route_performance()
        
        # RISK/CRITICAL queries
        if any(phrase in query_lower for phrase in ['critical', 'risk', 'at risk', 'urgent', 'alert', 'overdue']):
            return self._respond_risk_shipments()
        
        # Default: General overview
        return self._respond_overview()
    
    # ========== RESPONSE GENERATORS ==========
    
    def _respond_on_time_rate(self) -> Tuple[str, Dict[str, Any]]:
        """Generate on-time rate response"""
        metrics = self.analyzer.get_on_time_rate()
        
        # Handle missing status_breakdown
        if 'status_breakdown' not in metrics:
            status_breakdown = {
                'delivered': len(self.df[self.df['status'].str.upper() == 'DELIVERED']),
                'delayed': len(self.df[self.df['status'].str.upper() == 'DELAYED']),
                'in_transit': len(self.df[self.df['status'].str.upper() == 'IN_TRANSIT'])
            }
            metrics['status_breakdown'] = status_breakdown
        
        response = (
            f"On-Time Delivery Rate: {metrics['on_time_rate']}% ✅\n"
            f"• Delivered On-Time: {metrics['on_time_count']:,} shipments\n"
            f"• Total Delivered: {metrics['total_delivered']:,} shipments\n"
            f"• Late Deliveries: {metrics['delayed_count']:,} ({(metrics['delayed_count']/metrics['total_delivered']*100) if metrics['total_delivered'] > 0 else 0:.1f}%)\n"
            f"• Avg Late Days: {metrics['late_days_avg']} days\n"
            f"\nStatus Breakdown:\n"
            f"• Delivered: {metrics['status_breakdown']['delivered']:,}\n"
            f"• Delayed: {metrics['status_breakdown']['delayed']:,}\n"
            f"• In-Transit: {metrics['status_breakdown']['in_transit']:,}"
        )
        
        return response, {
            'query_type': 'on_time_rate',
            'metrics': metrics,
            'confidence': 0.99
        }
    
    def _respond_sku_count(self) -> Tuple[str, Dict[str, Any]]:
        """Generate SKU count response"""
        metrics = self.analyzer.get_sku_count()
        
        top_5 = metrics['top_5_skus']
        top_5_str = "\n".join([f"  {i+1}. {s['sku']}: {s['total_units']:,} units ({s['shipment_count']} shipments)" for i, s in enumerate(top_5)])
        
        response = (
            f"Total Unique SKUs: {metrics['total_skus']} 📦\n"
            f"• Total Units in System: {metrics['total_units']:,}\n"
            f"• Avg Units per SKU: {int(metrics['avg_units_per_sku']):,}\n"
            f"\nTop 5 SKUs by Volume:\n{top_5_str}"
        )
        
        return response, {
            'query_type': 'sku_count',
            'metrics': metrics,
            'confidence': 0.99
        }
    
    def _respond_shipment_details(self, shipment_id: str) -> Tuple[str, Dict[str, Any]]:
        """Generate shipment details response"""
        details = self.analyzer.get_shipment_details(shipment_id)
        
        if 'error' in details:
            return f"❌ {details['error']}", {'query_type': 'shipment_details', 'error': details['error']}
        
        response = (
            f"📦 {details['formatted_response']}\n"
            f"\nDetails:\n"
            f"• SKU: {details['sku']} | Quantity: {details['quantity']} units\n"
            f"• Route: {details['source']} → {details['destination']}\n"
            f"• Departed: {details['departed'].split()[0]}\n"
            f"• Expected: {details['expected_arrival'].split()[0]}\n"
            f"• Actual: {details['actual_arrival'].split()[0] if details['actual_arrival'] != 'N/A' else 'N/A'}\n"
            f"• Status: {details['status']}\n"
            f"• Risk Level: {details['risk_level']}"
        )
        
        return response, {
            'query_type': 'shipment_details',
            'shipment_id': shipment_id,
            'details': details,
            'confidence': 0.99
        }
    
    def _respond_location_shipments(self, location: str, is_source: bool = True) -> Tuple[str, Dict[str, Any]]:
        """Generate location shipments response"""
        metrics = self.analyzer.get_shipments_by_location(location, is_source)
        
        if 'error' in metrics:
            return f"⚠️ {metrics['error']}", {'query_type': 'location_shipments', 'error': metrics['error']}
        
        loc_type = "from" if is_source else "to"
        status_str = " | ".join([f"{k}: {v:,}" for k, v in metrics['status_breakdown'].items()])
        
        response = (
            f"Shipments {loc_type} {location}: {metrics['shipment_count']:,} 📦\n"
            f"• Total Units: {metrics['total_units']:,}\n"
            f"• On-Time Rate: {metrics['on_time_rate']}%\n"
            f"• Unique SKUs: {metrics['unique_skus']}\n"
            f"• Unique Routes: {metrics['unique_routes']}\n"
            f"\nStatus Breakdown:\n"
            f"• {status_str}"
        )
        
        return response, {
            'query_type': 'location_shipments',
            'location': location,
            'metrics': metrics,
            'confidence': 0.95
        }
    
    def _respond_route_performance(self) -> Tuple[str, Dict[str, Any]]:
        """Generate route performance response"""
        metrics = self.analyzer.get_route_performance(limit=5)
        
        routes_str = "\n".join([
            f"  {i+1}. {r['source']}→{r['destination']}: {r['on_time_rate']}% on-time ({r['shipment_count']} shipments)"
            for i, r in enumerate(metrics['top_routes'][:5])
        ])
        
        response = (
            f"Top Performing Routes: 🚚\n{routes_str}\n"
            f"\n✅ Best Route: {metrics['best_route']['source']}→{metrics['best_route']['destination']} ({metrics['best_route']['on_time_rate']}% on-time)\n"
            f"⚠️ Worst Route: {metrics['worst_route']['source']}→{metrics['worst_route']['destination']} ({metrics['worst_route']['on_time_rate']}% on-time)"
        )
        
        return response, {
            'query_type': 'route_performance',
            'metrics': metrics,
            'confidence': 0.98
        }
    
    def _respond_risk_shipments(self) -> Tuple[str, Dict[str, Any]]:
        """Generate risk shipments response"""
        metrics = self.analyzer.get_risk_shipments(limit=10)
        
        if metrics['critical_count'] == 0:
            response = "✅ No critical shipments at risk!"
        else:
            risk_str = "\n".join([
                f"  • {r['shipment_id']} | {r['sku']} | {r['source_location']}→{r['destination_location']} | {r['days_overdue']} days overdue"
                for r in metrics['risk_list'][:5]
            ])
            
            response = (
                f"🔴 CRITICAL ALERTS: {metrics['critical_shipments']} shipments at high risk\n"
                f"Total Delayed: {metrics['total_delayed']:,}\n\n"
                f"Top At-Risk Shipments:\n{risk_str}"
            )
        
        return response, {
            'query_type': 'risk_shipments',
            'metrics': metrics,
            'confidence': 0.98
        }
    
    def _respond_overview(self) -> Tuple[str, Dict[str, Any]]:
        """Generate general overview"""
        on_time = self.analyzer.get_on_time_rate()
        sku = self.analyzer.get_sku_count()
        loc = self.analyzer.get_location_analysis()
        
        # Handle missing status_breakdown
        if 'status_breakdown' not in on_time:
            status_breakdown = {
                'delivered': len(self.df[self.df['status'].str.upper() == 'DELIVERED']),
                'delayed': len(self.df[self.df['status'].str.upper() == 'DELAYED']),
                'in_transit': len(self.df[self.df['status'].str.upper() == 'IN_TRANSIT'])
            }
            on_time['status_breakdown'] = status_breakdown
        
        response = (
            f"Supply Chain Overview 📊\n"
            f"• Total Shipments: {len(self.df):,}\n"
            f"• On-Time Rate: {on_time['on_time_rate']}% ✅\n"
            f"• Unique SKUs: {sku['total_skus']}\n"
            f"• Source Locations: {loc['unique_source_locations']}\n"
            f"• Destination Locations: {loc['unique_destination_locations']}\n"
            f"• Active Routes: {loc['unique_routes']}\n"
            f"\nStatus Distribution:\n"
            f"• Delivered: {on_time['status_breakdown']['delivered']:,}\n"
            f"• Delayed: {on_time['status_breakdown']['delayed']:,}\n"
            f"• In-Transit: {on_time['status_breakdown']['in_transit']:,}"
        )
        
        return response, {
            'query_type': 'overview',
            'metrics': {
                'on_time': on_time,
                'sku': sku,
                'locations': loc
            },
            'confidence': 0.95
        }


if __name__ == "__main__":
    print("[OK] Improved Response Generator Ready")
    print("   Supports: on-time rate, SKU count, shipment details, location analysis, route performance, risk assessment")
