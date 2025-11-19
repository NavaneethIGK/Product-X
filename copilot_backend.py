from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime
from intent_detector import detect_intent, format_intent_for_summary
from query_engine import execute_query, QueryResult

app = FastAPI(title="Supply Chain AI Copilot", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
MODELS_PATH = r'C:\Projects\Prototypes\Product X\product-x-dashboard\public\models.json'

def load_models():
    try:
        with open(MODELS_PATH, 'r') as f:
            return json.load(f)
    except:
        return None

models = load_models()

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: Optional[list[ChatMessage]] = None
    query: str

class InsightRequest(BaseModel):
    insight_type: str  # 'delays', 'routes', 'skus', 'performance'
    top_n: int = 10

# Routes
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/models")
async def get_models():
    """Get loaded ML models and metrics"""
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")
    return models

@app.post("/insights")
async def get_insights(request: InsightRequest):
    """Get AI insights based on data analysis"""
    if not models:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    insights = {}
    
    if request.insight_type == "delays":
        route_stats = models.get('route_statistics', {})
        top_routes = sorted(
            route_stats.items(),
            key=lambda x: x[1].get('delay_rate', 0),
            reverse=True
        )[:request.top_n]
        insights['delayed_routes'] = [
            {
                'route': route,
                'delay_rate': stats.get('delay_rate', 0),
                'avg_delay_days': stats.get('avg_delay_days', 0),
                'total_shipments': stats.get('total_count', 0)
            }
            for route, stats in top_routes
        ]
    
    elif request.insight_type == "routes":
        route_stats = models.get('route_statistics', {})
        insights['routes'] = {
            route: {
                'expected_days': stats.get('expected_days', 0),
                'actual_days': stats.get('actual_days', 0),
                'total_shipments': stats.get('total_count', 0)
            }
            for route, stats in list(route_stats.items())[:request.top_n]
        }
    
    elif request.insight_type == "skus":
        sku_stats = models.get('sku_delays', {})
        insights['problematic_skus'] = [
            {
                'sku': sku,
                'delay_percentage': stats.get('delay_percentage', 0),
                'avg_delay': stats.get('avg_delay', 0),
                'avg_quantity': stats.get('avg_quantity', 0)
            }
            for sku, stats in list(sku_stats.items())[:request.top_n]
        ]
    
    elif request.insight_type == "performance":
        global_metrics = models.get('global_metrics', {})
        insights['summary'] = {
            'on_time_percentage': global_metrics.get('on_time_percentage', 0),
            'delay_percentage': global_metrics.get('delay_percentage', 0),
            'average_delay_days': global_metrics.get('average_delay_days', 0),
            'total_shipments_analyzed': global_metrics.get('total_shipments', 0)
        }
    
    return insights

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Structured Analytics Bot Pipeline:
    1. NLP Intent Detection (extract what user wants)
    2. Execute Structured Query (run analytics)
    3. Format Results (return structured JSON + readable summary)
    """
    user_query = request.query
    
    try:
        # Step 1: Detect intent from natural language query
        intent = detect_intent(user_query)
        print(f"🔍 Detected intent: {intent.query_type} (confidence: {intent.confidence})")
        
        # Step 2: Execute structured query based on intent
        query_result = execute_query(intent.query_type, limit=intent.limit)
        print(f"✅ Query result: {query_result.query_type}")
        
        # Step 3: Format response with structured data + readable summary
        response_text = f"**{query_result.summary}**\n\n"
        
        # Add structured metrics
        if query_result.result:
            response_text += "📊 **Key Metrics:**\n"
            for key, value in query_result.result.items():
                if isinstance(value, (int, float)):
                    formatted_key = key.replace('_', ' ').title()
                    response_text += f"• {formatted_key}: **{value}**\n"
        
        # Add data table summary
        if query_result.data:
            response_text += f"\n📋 **Top Results** ({len(query_result.data)} records):\n"
            for i, record in enumerate(query_result.data[:5], 1):
                # Format each record nicely
                record_items = [f"**{k}**: {v}" for k, v in record.items()]
                record_str = " | ".join(record_items)
                response_text += f"{i}. {record_str}\n"
            
            if len(query_result.data) > 5:
                response_text += f"\n... and {len(query_result.data) - 5} more records"
        
        return {
            "response": response_text,
            "intent": intent.query_type,
            "confidence": intent.confidence,
            "structured_data": {
                "query_type": query_result.query_type,
                "metrics": query_result.result,
                "records": query_result.data[:10],
                "total_records": len(query_result.data)
            },
            "sources": ["1M shipment CSV dataset"],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return {
            "response": f"⚠️ Error processing query: {str(e)}",
            "intent": "error",
            "confidence": 0.0,
            "structured_data": {},
            "sources": [],
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
