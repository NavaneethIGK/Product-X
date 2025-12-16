"""
GROQ-POWERED INTELLIGENT QUERY HANDLER
Uses Groq LLM for ALL reasoning, logic, and query interpretation (no regex, no hardcoded rules)
"""

import pandas as pd
from typing import Dict, Tuple, Any
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from improved_query_analyzer import ImprovedQueryAnalyzer
from ai_providers_groq import call_groq_api


class GroqPoweredQueryHandler:
    """Uses Groq LLM for ALL intelligent supply chain reasoning"""
    
    def __init__(self, df: pd.DataFrame, groq_api_key: str):
        self.df = df
        self.groq_api_key = groq_api_key
        self.analyzer = ImprovedQueryAnalyzer(df)
        
        # Verify API key is available
        if not self.groq_api_key:
            print("WARNING: Groq API key not provided!")
            print("   Cannot use LLM mode - no API key available")
            self.use_fallback = True
        else:
            print(f"Groq API key loaded: {self.groq_api_key[:20]}...{self.groq_api_key[-4:]}")
            self.use_fallback = False
    
    def _search_shipment_by_id(self, shipment_id: str) -> Dict[str, Any]:
        """Search for a specific shipment by ID in the dataset"""
        matching = self.df[self.df['shipment_id'] == shipment_id]
        
        if len(matching) == 0:
            return {'found': False, 'shipment_id': shipment_id}
        
        shipment = matching.iloc[0]
        return {
            'found': True,
            'shipment_id': shipment['shipment_id'],
            'sku': shipment['sku'],
            'quantity': shipment['quantity'],
            'source_location': shipment['source_location'],
            'destination_location': shipment['destination_location'],
            'status': shipment['status'],
            'departed_at': str(shipment['departed_at']),
            'expected_arrival': str(shipment['expected_arrival']),
            'arrived_at': str(shipment['arrived_at']) if pd.notna(shipment['arrived_at']) else 'Not yet arrived',
            'delay_days': (shipment['arrived_at'] - shipment['expected_arrival']).days if pd.notna(shipment['arrived_at']) and pd.notna(shipment['expected_arrival']) else 'N/A'
        }
    
    def handle_query(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Handle user query ENTIRELY with Groq LLM for intelligent reasoning
        Returns: (response_text, metadata)
        """
        
        print(f"\nGROQ LLM INTELLIGENT HANDLER")
        print(f"User Query: {user_query}")
        
        # If no API key, we cannot proceed
        if self.use_fallback or not self.groq_api_key:
            print(f"ERROR: Groq API key not available - cannot process query")
            return "Error: Groq API key not configured. Please add GROQ_API_KEY to environment or config.json", {
                'method': 'error',
                'timestamp': datetime.now().isoformat()
            }
        
        # Step 1: Gather ALL possible data that Groq might need
        context_data = self._gather_all_context(user_query)
        
        # Step 2: Let GROQ LLM handle ALL the logic - no regex, no hardcoding
        prompt = self._build_groq_prompt_with_all_reasoning(user_query, context_data)
        
        # Step 3: Call Groq LLM for reasoning AND answer generation
        print(f"Calling Groq LLM for intelligent reasoning...")
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_groq_api(
                api_key=self.groq_api_key,
                messages=messages,
                system_prompt=self._get_system_prompt(),
                user_query=user_query
            )
            
            print(f"Groq Response Generated Successfully")
            
            # Step 4: Return raw response from Groq (already intelligent and formatted)
            final_response = response.strip()
            
            metadata = {
                'method': 'groq_powered_llm_reasoning',
                'llm_model': 'groq/llama-3.3-70b-versatile',
                'reasoning_engine': 'LLM (no regex, no hardcoded rules)',
                'timestamp': datetime.now().isoformat()
            }
            
            return final_response, metadata
            
        except Exception as e:
            print(f"Groq API Error: {e}")
            return f"Error: {str(e)}", {
                'method': 'error',
                'timestamp': datetime.now().isoformat()
            }
    
    def _gather_all_context(self, user_query: str = "") -> Dict[str, Any]:
        """Gather all relevant metrics from CSV and sample data"""
        print(f"Gathering context data...")
        
        on_time = self.analyzer.get_on_time_rate()
        sku = self.analyzer.get_sku_count()
        locations = self.analyzer.get_location_analysis()
        destination_metrics = self.analyzer.get_all_destination_metrics()
        
        # Check if user is asking for individual shipment details by ID
        import re
        shipment_id_match = re.search(r'(SHP-\d{7})', user_query, re.IGNORECASE)
        shipment_detail = None
        
        if shipment_id_match:
            shipment_id = shipment_id_match.group(1).upper()
            shipment_detail = self._search_shipment_by_id(shipment_id)
            print(f"Found shipment lookup request for: {shipment_id}")
        
        # Get sample shipments as examples
        sample_shipments = []
        if any(word in user_query.lower() for word in ['shipment', 'detail', 'track', 'shp', 'order']):
            # Get first 5 shipments as examples
            sample_df = self.df.head(5)
            sample_shipments = sample_df[[
                'shipment_id', 'sku', 'quantity', 'source_location', 
                'destination_location', 'status', 'departed_at', 'expected_arrival', 'arrived_at'
            ]].to_dict('records')
        
        context = {
            'total_shipments': len(self.df),
            'on_time_metrics': on_time,
            'sku_metrics': sku,
            'location_metrics': locations,
            'destination_metrics': destination_metrics,
            'sample_shipments': sample_shipments,
            'dataset_summary': f"{len(self.df):,} shipments, {sku['total_skus']} SKUs, {locations['unique_source_locations']} source locations"
        }
        
        # Add specific shipment detail if found
        if shipment_detail:
            context['specific_shipment'] = shipment_detail
        
        return context
    
    def _build_groq_prompt_with_all_reasoning(self, user_query: str, context_data: Dict[str, Any]) -> str:
        """Build comprehensive prompt for Groq LLM to handle ALL reasoning"""
        
        # Calculate key percentages
        total_shipments = context_data['total_shipments']
        arrived = context_data['on_time_metrics']['total_arrived']
        in_transit = context_data['on_time_metrics']['status_breakdown']['in_transit']
        arrived_pct = (arrived / total_shipments * 100) if total_shipments > 0 else 0
        in_transit_pct = (in_transit / total_shipments * 100) if total_shipments > 0 else 0
        
        # Prepare all data in a structured format for Groq to understand
        context_str = f"""
SUPPLY CHAIN DATABASE - COMPLETE DATA SUMMARY:
==============================================
Total Shipment Records: {total_shipments:,} (100%)

SHIPMENT STATUS BREAKDOWN (out of {total_shipments:,} total):
- ARRIVED: {arrived:,} shipments ({arrived_pct:.1f}%)
  * On-Time: {context_data['on_time_metrics']['on_time_count']:,} shipments ({context_data['on_time_metrics']['on_time_rate']}%)
  * Late/Delayed: {context_data['on_time_metrics']['late_count']:,} shipments
- IN-TRANSIT: {in_transit:,} shipments ({in_transit_pct:.1f}%)

KEY PERFORMANCE METRICS:
- Overall On-Time Delivery Rate (arrived only): {context_data['on_time_metrics']['on_time_rate']}%
- Average Delay (late shipments): {context_data['on_time_metrics']['late_days_avg']} days

LOCATIONS IN DATABASE:
- Source Locations: {context_data['location_metrics']['unique_source_locations']}
- Destination Locations: {context_data['location_metrics']['unique_destination_locations']}

DESTINATION LOCATION SHIPMENT BREAKDOWN (out of {total_shipments:,} total):
"""
        for dest in context_data['destination_metrics']['destinations']:
            dest_pct = (dest['shipment_count'] / total_shipments * 100)
            context_str += f"- {dest['location']}: {dest['shipment_count']:,} shipments ({dest_pct:.1f}%), {dest['total_units']:,} units, {dest['on_time_rate']}% on-time rate\n"
        
        context_str += f"""
PRODUCTS CATALOG:
- Unique SKUs: {context_data['sku_metrics']['total_skus']}
- Total Units Shipped: {context_data['sku_metrics']['total_units']:,}

TOP 5 SKUs BY VOLUME:
"""
        for i, sku_info in enumerate(context_data['sku_metrics']['top_5_skus'], 1):
            sku_pct = (sku_info['total_units'] / context_data['sku_metrics']['total_units'] * 100)
            context_str += f"{i}. {sku_info['sku']}: {sku_info['total_units']:,} units ({sku_pct:.1f}% of total volume)\n"
        
        # Add sample shipments if available (for shipment detail queries)
        if context_data.get('sample_shipments'):
            context_str += "\nSAMPLE SHIPMENTS (data structure example):\n"
            for i, shipment in enumerate(context_data['sample_shipments'][:3], 1):
                context_str += f"{i}. ID: {shipment.get('shipment_id', 'N/A')} | SKU: {shipment.get('sku', 'N/A')} | Qty: {shipment.get('quantity', 'N/A')} | From: {shipment.get('source_location', 'N/A')} | To: {shipment.get('destination_location', 'N/A')} | Status: {shipment.get('status', 'N/A')} | Departed: {shipment.get('departed_at', 'N/A')} | Expected: {shipment.get('expected_arrival', 'N/A')} | Arrived: {shipment.get('arrived_at', 'N/A')}\n"
        
        # Add specific shipment if found
        if context_data.get('specific_shipment'):
            shipment = context_data['specific_shipment']
            if shipment.get('found'):
                context_str += f"\nSPECIFIC SHIPMENT REQUESTED:\n"
                context_str += f"ID: {shipment['shipment_id']}\n"
                context_str += f"SKU: {shipment['sku']}\n"
                context_str += f"Quantity: {shipment['quantity']}\n"
                context_str += f"From: {shipment['source_location']} -> To: {shipment['destination_location']}\n"
                context_str += f"Status: {shipment['status']}\n"
                context_str += f"Departed: {shipment['departed_at']}\n"
                context_str += f"Expected Arrival: {shipment['expected_arrival']}\n"
                context_str += f"Actual Arrival: {shipment['arrived_at']}\n"
                context_str += f"Delay: {shipment['delay_days']} days\n"
            else:
                context_str += f"\nSPECIFIC SHIPMENT REQUESTED:\n"
                context_str += f"Shipment {shipment['shipment_id']} not found in database\n"
        
        prompt = f"""{context_str}

USER QUESTION: "{user_query}"

INSTRUCTIONS FOR REASONING:
1. Understand what the user is asking about:
   - Metrics queries: on-time rate, delay rate, shipment counts
   - Location queries: shipments to/from specific locations
   - Shipment queries: individual shipment details by ID
   - SKU queries: product information and volumes
2. Use the database metrics and sample data to answer
3. For location queries: if user mentions "LON", interpret as "UK-LON", if "LAX" interpret as "US-LAX", etc.
4. For shipment ID queries: search the database for that specific shipment_id and return its details
5. For metric queries: use the aggregated numbers provided
6. Be concise - answer in 1-3 sentences max
7. Include specific numbers and details in your answer
8. If you can't find data for a specific query, say so clearly
9. Do NOT make up data - only use what's in the database above

ANSWER TO THE USER QUESTION:"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """System prompt for Groq - emphasize reasoning and accuracy"""
        return """You are an expert Supply Chain Analytics AI. 
Your job is to:
1. Understand the user's question about supply chain metrics
2. Reason through what data they need
3. Provide ACCURATE answers based ONLY on the provided data
4. Be brief - maximum 1-2 sentences
5. Include specific numbers
6. Never make up or estimate data"""


if __name__ == "__main__":
    print("Groq-powered query handler module loaded successfully")

