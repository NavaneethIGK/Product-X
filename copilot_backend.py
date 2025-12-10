from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
from openai import OpenAI
from intent_detector import detect_intent, QueryIntent
from query_engine import execute_query, QueryResult

app = FastAPI(title="Supply Chain AI Copilot", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://103.174.10.207:5000",
        "http://103.174.10.207:8000",
        "https://103.174.10.207:5000",
        "https://103.174.10.207:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration system for OpenAI API Key
class ConfigManager:
    def __init__(self):
        self.api_key = None
        self.load_config()
    
    def load_config(self):
        """Load API key from environment variable or config file"""
        # Priority 1: Environment variable
        if os.getenv('OPENAI_API_KEY'):
            self.api_key = os.getenv('OPENAI_API_KEY')
            print("✅ OpenAI API Key loaded from OPENAI_API_KEY environment variable")
            return
        
        # Priority 2: .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            print("✅ OpenAI API Key loaded from .env file")
                            return
            except Exception as e:
                print(f"⚠️  Error reading .env file: {e}")
        
        # Priority 3: config.json file
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if 'openai_api_key' in config:
                        self.api_key = config['openai_api_key']
                        print("✅ OpenAI API Key loaded from config.json")
                        return
            except Exception as e:
                print(f"⚠️  Error reading config.json: {e}")
        
        print("⚠️  OpenAI API Key not configured. Set OPENAI_API_KEY environment variable or create config.json/. env file")
    
    def set_api_key(self, api_key: str):
        """Dynamically set API key at runtime"""
        self.api_key = api_key
        print(f"✅ OpenAI API Key updated (length: {len(api_key)})")
    
    def get_client(self):
        """Get OpenAI client with current API key"""
        if self.api_key:
            return OpenAI(api_key=self.api_key)
        return None

# Initialize configuration manager
config_manager = ConfigManager()
client = config_manager.get_client()

print(f"🤖 OpenAI Configured: {client is not None}")

# Load models
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(SCRIPT_DIR, 'product-x-dashboard', 'public', 'models.json')

def load_models():
    try:
        with open(MODELS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Could not load models from {MODELS_PATH}: {e}")
        return None

models = load_models()

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    query: str

class InsightRequest(BaseModel):
    insight_type: str
    top_n: int = 10

class ConfigRequest(BaseModel):
    openai_api_key: str

class ConfigResponse(BaseModel):
    message: str
    openai_configured: bool

# Routes
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": client is not None
    }

@app.get("/config")
async def get_config():
    """Get current configuration status"""
    return {
        "openai_configured": config_manager.api_key is not None,
        "api_key_length": len(config_manager.api_key) if config_manager.api_key else 0,
        "api_key_preview": f"{config_manager.api_key[:20]}...{config_manager.api_key[-4:]}" if config_manager.api_key else "Not configured"
    }

@app.post("/config/openai")
async def set_openai_config(request: ConfigRequest):
    """Set OpenAI API key dynamically"""
    try:
        config_manager.set_api_key(request.openai_api_key)
        global client
        client = config_manager.get_client()
        return ConfigResponse(
            message="✅ OpenAI API key configured successfully",
            openai_configured=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to configure API key: {str(e)}")

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

def generate_insights(user_query: str, intent: QueryIntent, query_result: QueryResult) -> str:
    """Generate AI insights using OpenAI with proper context shaping"""
    
    if not config_manager.api_key:
        return f"📊 {query_result.summary}"
    
    try:
        from data_enrichment import enrich_shipment
        from llm_context import (
            build_shipment_context, build_aggregated_context,
            get_system_prompt_for_intent, generate_guaranteed_insights
        )
        
        current_client = config_manager.get_client()
        if not current_client:
            return f"📊 {query_result.summary}"
        
        # Build LLM context based on query type
        llm_context = None
        system_prompt = get_system_prompt_for_intent(intent.query_type)
        
        # For single shipment queries, enrich the data
        if intent.query_type == 'shipment_details' and query_result.data:
            try:
                enriched = enrich_shipment(query_result.data[0])
                llm_context = build_shipment_context(enriched)
            except Exception as e:
                print(f"⚠️ Enrichment error: {e}")
                llm_context = {"raw_data": query_result.data}
        
        # For aggregate queries, build aggregated context
        elif query_result.data and len(query_result.data) > 1:
            enriched_list = []
            for record in query_result.data[:20]:  # Limit to 20 for performance
                try:
                    enriched_list.append(enrich_shipment(record))
                except:
                    pass
            if enriched_list:
                llm_context = build_aggregated_context(enriched_list, intent.query_type)
        
        # Fallback to raw context if enrichment fails
        if not llm_context:
            llm_context = {
                "query_type": intent.query_type,
                "summary": query_result.summary,
                "metrics": query_result.result,
                "data_points": len(query_result.data) if query_result.data else 0
            }
        
        # Extract LLM context string if available (from enriched shipment)
        llm_context_str = llm_context.get("llm_context", None) if isinstance(llm_context, dict) else None
        
        # Build prompt with context shaping
        if llm_context_str:
            # Use professional, structured context from enrichment layer
            context_for_llm = llm_context_str
        else:
            # Fallback to JSON context
            context_for_llm = f"""SHIPMENT DATA CONTEXT:
{json.dumps(llm_context, indent=2, default=str)}"""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"""Analyze this shipment information and respond according to your professional guidelines:

{context_for_llm}

Customer Query: {user_query}

Provide a professional, insightful response that:
1. Summarizes the shipment status clearly
2. Explains the timeline and any delays
3. Assesses risk level 
4. Provides specific next steps and recommendations
5. Uses human-friendly language
6. Never says "data not available" - infer from available information"""
            }
        ]
        
        print(f"🤖 Calling OpenAI API with professional context shaping...")
        print(f"   Model: gpt-3.5-turbo")
        print(f"   API Key: {config_manager.api_key[:20]}...{config_manager.api_key[-4:]}")
        
        response = current_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1200,
            top_p=0.9
        )
        
        ai_response = response.choices[0].message.content
        print(f"✨ AI Response Generated from OpenAI")
        print(f"   Tokens used: {response.usage.total_tokens}")
        return ai_response
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ OpenAI Error: {error_msg}")
        
        # Handle specific error types gracefully
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            print(f"⚠️ API Quota exceeded. Generating expert insights without OpenAI...")
            return generate_expert_fallback_response(intent, query_result)
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print(f"⚠️ API authentication failed. Using fallback mode...")
            return generate_expert_fallback_response(intent, query_result)
        else:
            # Other errors
            import traceback
            traceback.print_exc()
            return generate_expert_fallback_response(intent, query_result)


def generate_expert_fallback_response(intent: QueryIntent, query_result: QueryResult) -> str:
    """Generate professional expert response WITHOUT OpenAI
    
    Uses enriched data to create insightful, human-friendly responses
    when API is unavailable.
    """
    try:
        from data_enrichment import enrich_shipment
        
        response_parts = []
        
        if intent.query_type == 'shipment_details' and query_result.data:
            # Single shipment analysis
            try:
                enriched = enrich_shipment(query_result.data[0])
                
                response_parts.append("## 📦 SHIPMENT STATUS ANALYSIS\n")
                response_parts.append(f"**Shipment ID:** {enriched.shipment_id}\n")
                response_parts.append(f"**Status:** {enriched.status_label}\n\n")
                
                response_parts.append("### 📅 Timeline\n")
                response_parts.append(f"- Shipped: {enriched.shipped_date}\n")
                response_parts.append(f"- Expected Arrival: {enriched.expected_arrival}\n")
                if enriched.actual_arrival:
                    response_parts.append(f"- Actual Arrival: {enriched.actual_arrival}\n")
                response_parts.append(f"- Transit Days: {enriched.transit_days or 'In progress'}\n")
                response_parts.append(f"- Delay: {enriched.delay_days or 0} days\n\n")
                
                response_parts.append("### 📍 Route & Cargo\n")
                response_parts.append(f"- Route: {enriched.source} → {enriched.destination}\n")
                response_parts.append(f"- SKU: {enriched.sku} (Qty: {enriched.quantity} units)\n\n")
                
                response_parts.append("### ⚠️ Risk Assessment\n")
                risk_level = "HIGH 🔴" if enriched.risk_score > 0.7 else "MEDIUM 🟡" if enriched.risk_score > 0.4 else "LOW 🟢"
                response_parts.append(f"- Risk Level: {risk_level}\n")
                response_parts.append(f"- Health Status: {enriched.shipment_health}\n")
                if enriched.estimated_delay_reason:
                    response_parts.append(f"- Delay Reason: {enriched.estimated_delay_reason}\n\n")
                
                response_parts.append("### ✅ Recommendations\n")
                for i, rec in enumerate(enriched.recommendations[:3], 1):
                    response_parts.append(f"{i}. {rec}\n")
                
            except Exception as e:
                print(f"Enrichment error in fallback: {e}")
                response_parts.append(query_result.summary)
        
        elif query_result.data:
            # Multi-shipment analysis
            response_parts.append(f"## 📊 ANALYSIS: {query_result.summary}\n\n")
            response_parts.append("### 🔍 Key Findings\n")
            
            if query_result.result:
                for key, value in query_result.result.items():
                    response_parts.append(f"- **{key}**: {value}\n")
            
            response_parts.append("\n### 📈 Top Items\n")
            for i, item in enumerate(query_result.data[:5], 1):
                if isinstance(item, dict):
                    summary = " | ".join([f"{k}: {v}" for k, v in list(item.items())[:3]])
                    response_parts.append(f"{i}. {summary}\n")
        
        else:
            response_parts.append(query_result.summary)
        
        response_parts.append("\n\n_📝 Note: Response generated using enriched data analysis (OpenAI service temporarily unavailable)_")
        
        return "".join(response_parts)
    
    except Exception as e:
        print(f"Fallback generation error: {e}")
        return query_result.summary

def format_response(ai_insights: str, query_result: QueryResult) -> str:
    """Format final response with insights and data"""
    
    response = f"🤖 **AI Analysis:**\n{ai_insights}\n\n"
    
    if query_result.data:
        response += f"📋 **Detailed Data** ({len(query_result.data)} records):\n"
        for i, record in enumerate(query_result.data[:5], 1):
            record_str = " | ".join([f"**{k}**: {v}" for k, v in record.items()])
            response += f"{i}. {record_str}\n"
    
    response += f"\n📊 **Summary**: {query_result.summary}"
    
    return response

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    🤖 AI-Powered Supply Chain Copilot
    
    Process:
    1. Detect user intent (SKU, Route, Delay, Location, etc.)
    2. Execute structured query on CSV data
    3. Use OpenAI to generate proactive insights
    4. Return formatted response with recommendations
    """
    user_query = request.query
    
    try:
        print(f"📥 User Query: {user_query}")
        
        # Step 1: Detect intent
        intent = detect_intent(user_query)
        if intent is None:
            intent = QueryIntent(query_type='summary_stats', filters={}, confidence=0.5)
        
        print(f"🔍 Detected Intent: {intent.query_type} (confidence: {intent.confidence})")
        
        # Step 2: Execute structured query with filters
        query_result = execute_query(intent.query_type, limit=intent.limit, **intent.filters)
        
        print(f"✅ Query Result: {query_result.query_type}")
        
        # Step 3: Generate AI-powered insights
        ai_insights = generate_insights(user_query, intent, query_result)
        
        # Step 4: Format response
        response_text = format_response(ai_insights, query_result)
        
        return {
            "response": response_text,
            "intent": intent.query_type,
            "confidence": intent.confidence,
            "structured_data": {
                "query_type": query_result.query_type,
                "metrics": query_result.result,
                "records": query_result.data[:10] if query_result.data else []
            },
            "ai_powered": True,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        
        return {
            "response": f"⚠️ Error processing query: {str(e)}",
            "intent": "error",
            "confidence": 0.0,
            "structured_data": None,
            "ai_powered": False,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Load models
# Path relative to script location - works on both Windows and Linux
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(SCRIPT_DIR, 'product-x-dashboard', 'public', 'models.json')

def load_models():
    try:
        with open(MODELS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Could not load models from {MODELS_PATH}: {e}")
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
        
        # Safety check - ensure intent is not None
        if intent is None:
            intent = QueryIntent(query_type='summary_stats', filters={}, confidence=0.5)
        
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
