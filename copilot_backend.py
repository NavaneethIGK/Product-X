from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
from intent_detector import detect_intent, QueryIntent
from query_engine import execute_query, QueryResult
from ai_providers_openai import call_openai_api, get_openai_client
from ai_providers_groq import call_groq_api

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

# Configuration system for OpenAI & Groq API Keys
class ConfigManager:
    def __init__(self):
        self.openai_api_key = None
        self.grok_api_key = None
        self.use_grok = False  # Default to OpenAI
        self.load_config()
    
    def load_config(self):
        """Load API keys and provider preference from config.json (Priority 1) or environment (Priority 2)"""
        # Priority 1: config.json file
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # New config format
                    if 'ai_provider' in config:
                        # New structured format
                        ai_provider_config = config.get('ai_provider', {})
                        provider = ai_provider_config.get('provider', 'groq').lower()
                        
                        # Load OpenAI config
                        openai_config = config.get('openai', {})
                        if openai_config.get('enabled') and openai_config.get('api_key'):
                            self.openai_api_key = openai_config['api_key']
                            print("✅ OpenAI API Key loaded from config.json")
                        
                        # Load Groq config
                        groq_config = config.get('groq', {})
                        if groq_config.get('enabled') and groq_config.get('api_key'):
                            self.grok_api_key = groq_config['api_key']
                            print("✅ Groq API Key loaded from config.json")
                        
                        # Set provider
                        self.use_grok = provider == 'groq'
                        print(f"✅ AI Provider set to: {'GROQ' if self.use_grok else 'OPENAI'} (from config.json)")
                    else:
                        # Legacy config format for backward compatibility
                        if config.get('openai_api_key'):
                            self.openai_api_key = config['openai_api_key']
                            print("✅ OpenAI API Key loaded from config.json")
                        
                        if config.get('grok_api_key'):
                            self.grok_api_key = config['grok_api_key']
                            print("✅ Groq API Key loaded from config.json")
                        
                        if 'use_grok' in config:
                            self.use_grok = config.get('use_grok', False)
                            print(f"✅ AI Provider set to: {'GROQ' if self.use_grok else 'OPENAI'} (from config.json)")
            except Exception as e:
                print(f"⚠️  Error reading config.json: {e}")
        
        # Priority 2: Environment variables (override config.json)
        if os.getenv('OPENAI_API_KEY'):
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            print("✅ OpenAI API Key loaded from OPENAI_API_KEY environment variable")
        
        if os.getenv('GROQ_API_KEY'):
            self.grok_api_key = os.getenv('GROQ_API_KEY')
            print("✅ Groq API Key loaded from GROQ_API_KEY environment variable")
        
        if os.getenv('AI_PROVIDER'):
            provider = os.getenv('AI_PROVIDER').lower()
            self.use_grok = provider == 'groq'
            print(f"✅ AI Provider set to: {'GROQ' if self.use_grok else 'OPENAI'} (from environment)")
        
        # Print summary
        print(f"\n📊 AI Configuration Summary:")
        print(f"  OpenAI Available: {bool(self.openai_api_key)}")
        print(f"  Groq Available: {bool(self.grok_api_key)}")
        print(f"  Current Provider: {'🦅 GROQ' if self.use_grok else '🤖 OPENAI'}")
        
        if not self.openai_api_key and not self.grok_api_key:
            print(f"\n⚠️  Warning: No AI providers configured!")
            print(f"  Update config.json with your API keys and set 'enabled: true'")
            print(f"  Or set OPENAI_API_KEY or GROQ_API_KEY environment variables")
    
    def set_openai_key(self, api_key: str):
        """Dynamically set OpenAI API key"""
        self.openai_api_key = api_key
        print(f"✅ OpenAI API Key updated (length: {len(api_key)})")
    
    def set_grok_key(self, api_key: str):
        """Dynamically set Groq API key"""
        self.grok_api_key = api_key
        print(f"✅ Groq API Key updated (length: {len(api_key)})")
    
    def set_provider(self, use_grok: bool):
        """Switch between OpenAI (False) and Groq (True)"""
        self.use_grok = use_grok
        provider_name = "🦅 GROQ" if use_grok else "🤖 OPENAI"
        print(f"✅ AI Provider switched to: {provider_name}")
    
    def get_openai_client(self):
        """Get OpenAI client"""
        if self.openai_api_key:
            return get_openai_client(self.openai_api_key)
        return None
    
    def get_current_provider(self):
        """Get name of current provider"""
        if self.use_grok:
            return "grok" if self.grok_api_key else None
        else:
            return "openai" if self.openai_api_key else None
    
    def is_configured(self):
        """Check if at least one provider is configured"""
        return bool(self.openai_api_key or self.grok_api_key)

# Initialize configuration manager
config_manager = ConfigManager()
client = config_manager.get_openai_client() if not config_manager.use_grok else None

print(f"\n🚀 AI Copilot Initialized")
print(f"   Current Provider: {'🦅 GROQ' if config_manager.use_grok else '🤖 OPENAI'}")
print(f"   Configured: {config_manager.is_configured()}")

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
    openai_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None
    use_grok: Optional[bool] = None

class ConfigResponse(BaseModel):
    message: str
    provider: str
    configured: bool

# Routes
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "current_provider": config_manager.get_current_provider(),
        "openai_available": bool(config_manager.openai_api_key),
        "grok_available": bool(config_manager.grok_api_key),
        "is_configured": config_manager.is_configured()
    }

@app.get("/config")
async def get_config():
    """Get current configuration status"""
    return {
        "current_provider": "🦅 GROQ" if config_manager.use_grok else "🤖 OPENAI",
        "openai_configured": bool(config_manager.openai_api_key),
        "openai_preview": f"{config_manager.openai_api_key[:20]}...{config_manager.openai_api_key[-4:]}" if config_manager.openai_api_key else "Not configured",
        "groq_configured": bool(config_manager.grok_api_key),
        "groq_preview": f"{config_manager.grok_api_key[:20]}...{config_manager.grok_api_key[-4:]}" if config_manager.grok_api_key else "Not configured",
        "use_grok_setting": config_manager.use_grok
    }

@app.post("/config/provider")
async def set_provider_config(request: ConfigRequest):
    """Configure AI provider (OpenAI or Groq) with optional API keys"""
    try:
        message_parts = []
        
        # Set API keys if provided
        if request.openai_api_key:
            config_manager.set_openai_key(request.openai_api_key)
            message_parts.append("✅ OpenAI API key configured")
        
        if request.grok_api_key:
            config_manager.set_grok_key(request.grok_api_key)
            message_parts.append("✅ Groq API key configured")
        
        # Switch provider if requested
        if request.use_grok is not None:
            config_manager.set_provider(request.use_grok)
            provider_name = "🦅 GROQ" if request.use_grok else "🤖 OPENAI"
            message_parts.append(f"Provider switched to: {provider_name}")
        
        global client
        client = config_manager.get_openai_client() if not config_manager.use_grok else None
        
        return ConfigResponse(
            message=" | ".join(message_parts) if message_parts else "Configuration unchanged",
            provider="🦅 GROQ" if config_manager.use_grok else "🤖 OPENAI",
            configured=config_manager.is_configured()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to configure provider: {str(e)}")

@app.post("/config/openai")
async def set_openai_config(request: ConfigRequest):
    """Set OpenAI API key dynamically (legacy endpoint)"""
    try:
        if not request.openai_api_key:
            raise ValueError("openai_api_key is required")
        
        config_manager.set_openai_key(request.openai_api_key)
        config_manager.set_provider(False)  # Switch to OpenAI
        global client
        client = config_manager.get_openai_client()
        
        return ConfigResponse(
            message="✅ OpenAI API key configured successfully",
            provider="🤖 OPENAI",
            configured=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to configure API key: {str(e)}")

@app.post("/config/groq")
async def set_groq_config(request: ConfigRequest):
    """Set Groq API key dynamically"""
    try:
        if not request.grok_api_key:
            raise ValueError("grok_api_key is required")
        
        config_manager.set_grok_key(request.grok_api_key)
        config_manager.set_provider(True)  # Switch to Groq
        global client
        client = None  # Groq doesn't use OpenAI client
        
        return ConfigResponse(
            message="✅ Groq API key configured successfully",
            provider="🦅 GROQ",
            configured=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to configure Groq: {str(e)}")

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
    """Generate AI insights using configured provider (OpenAI or Groq)"""
    
    # Check if any provider is configured
    if not config_manager.is_configured():
        print("⚠️ No AI providers configured. Using fallback...")
        return generate_expert_fallback_from_query(intent, query_result)
    
    try:
        from data_enrichment import enrich_shipment
        from llm_context import (
            build_shipment_context, build_aggregated_context,
            get_system_prompt_for_intent, generate_guaranteed_insights
        )
        
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
            context_for_llm = llm_context_str
        else:
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
        
        # USE GROQ
        if config_manager.use_grok:
            from ai_providers_groq import call_groq_api
            return call_groq_api(config_manager.grok_api_key, messages, system_prompt, user_query)
        
        # USE OPENAI
        else:
            from ai_providers_openai import call_openai_api
            return call_openai_api(config_manager.openai_api_key, messages, user_query)
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Error: {error_msg}")
        import traceback
        traceback.print_exc()
        # Use fallback for this query
        return generate_expert_fallback_from_query(intent, query_result)


def generate_expert_fallback_from_query(intent: Optional[QueryIntent], query_result: Optional[QueryResult]) -> str:
    """Generate concise response answering exactly what user asked (no AI service)"""
    
    if intent is None or query_result is None:
        return "⚠️ Service temporarily unavailable."
    
    try:
        from data_enrichment import enrich_shipment
        
        # SHIPMENT DETAILS - Show only what's requested
        if intent.query_type == 'shipment_details' and query_result.data:
            try:
                enriched = enrich_shipment(query_result.data[0])
                
                response = f"**{enriched.shipment_id}** - {enriched.status_label}\n"
                response += f"📦 {enriched.sku} ({enriched.quantity} units) | {enriched.source} → {enriched.destination}\n"
                response += f"📅 Shipped: {enriched.shipped_date_short} | Expected: {enriched.expected_arrival_short}\n"
                
                if enriched.actual_arrival:
                    response += f"✅ Delivered: {enriched.actual_arrival_short} ({enriched.transit_days} days)\n"
                else:
                    response += f"⏳ In Transit ({enriched.delay_days if enriched.delay_days else 0} days overdue)\n"
                
                risk_emoji = "🔴" if enriched.risk_score > 0.7 else "🟡" if enriched.risk_score > 0.4 else "🟢"
                response += f"{risk_emoji} Risk: {'HIGH' if enriched.risk_score > 0.7 else 'MEDIUM' if enriched.risk_score > 0.4 else 'LOW'}\n"
                
                if enriched.recommendations:
                    response += f"\n**Next Steps:**\n"
                    for i, rec in enumerate(enriched.recommendations[:1], 1):
                        response += f"{i}. {rec}\n"
                
                return response
            except Exception as e:
                return query_result.summary
        
        # MULTI-SHIPMENT ANALYSIS - Show only the metrics user asked for
        elif query_result.data:
            response = f"**{query_result.summary}**\n\n"
            
            if query_result.result:
                for key, value in list(query_result.result.items())[:5]:  # Top 5 metrics only
                    response += f"• {key}: {value}\n"
            
            return response
        
        else:
            return query_result.summary
    
    except Exception as e:
        print(f"Error: {e}")
        return query_result.summary if query_result else "⚠️ Analysis unavailable."

def format_response(ai_insights: str, query_result: QueryResult) -> str:
    """Format final response - CONCISE & DIRECT (only what user asked)"""
    
    # Just return the AI insights - no extra sections
    return ai_insights

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
