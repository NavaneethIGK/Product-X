from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import os
import uuid
import jwt
import pandas as pd
from intent_detector import detect_intent, QueryIntent
from query_engine import execute_query, QueryResult, load_csv
from ai_providers_openai import call_openai_api, get_openai_client
from ai_providers_groq import call_groq_api
from smart_query_engine import smart_parse_intent, execute_smart_query, format_for_response
from auth_db import verify_password, get_user, init_db, create_default_user
from improved_response_generator import ImprovedResponseGenerator

# Session management for conversation history
class ConversationSession:
    """Manages conversation history for a user session"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, str]] = []  # List of {role, content} dicts
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.context: Dict[str, Any] = {}  # Store extracted entities/context
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get last N messages (for API context)"""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages[-limit:]]
    
    def update_context(self, key: str, value: Any):
        """Store session context (extracted entities, preferences, etc.)"""
        self.context[key] = value
    
    def get_system_prompt(self) -> str:
        """Generate system prompt with session context - ENFORCE MAXIMUM CONCISENESS"""
        # Build context of what was already discussed
        context_items = []
        if self.context.get('last_shipment_id'):
            context_items.append(f"Previously discussed: {self.context['last_shipment_id']}")
        if self.context.get('last_sku'):
            context_items.append(f"SKU: {self.context['last_sku']}")
        
        context_reminder = " | ".join(context_items) if context_items else "First question"
        
        base_prompt = f"""You are a Supply Chain AI Assistant. SPEAK LIKE AN EXPERT LOGISTICS MANAGER.

CONSTRAINTS (MUST FOLLOW):
✓ MAXIMUM 2-3 sentences per answer
✓ Answer ONLY what was asked - NO extra context or explanations
✓ If follow-up to previous message, do NOT repeat previously stated facts
✓ Use precise data only - no assumptions
✓ For shipment details: "SHP-ID | SKU (qty) | Source→Dest | Status | Risk"
✓ Never say "I don't have data" - use reasonable inferences
✓ Format concisely: use emoji and abbreviations (📦=cargo, 📅=date, ⚠️=risk, etc.)

CONVERSATION CONTEXT:
{context_reminder}
Messages so far: {len(self.messages)}

RESPONSE STYLE:
- Follow-up about SHP-0000014 source? Answer: "IN-DEL→IN-DEL"
- Follow-up asking for risk? Answer: "🔴 HIGH - Overdue 5+ days"
- Do NOT repeat what was already said 3 messages ago
- Assume user knows previous context unless asking for clarification"""

        return base_prompt

# Global session storage (in production, use Redis or database)
sessions: Dict[str, ConversationSession] = {}

# ============================================================================
# AUTHENTICATION SETUP
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Pydantic models for auth
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_email: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Initialize auth DB
init_db()
create_default_user()

def create_access_token(email: str) -> str:
    """Create JWT token for user"""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return email"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        return email
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(token: Optional[str] = None) -> str:
    """Dependency to verify token from Authorization header"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return email


def get_or_create_session(session_id: Optional[str] = None) -> ConversationSession:
    """Get existing session or create new one"""
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = ConversationSession(session_id)
    return sessions[session_id]

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

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password, return JWT token"""
    email = request.email
    password = request.password
    
    # Verify credentials
    if not verify_password(email, password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = create_access_token(email)
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_email=email
    )

@app.post("/auth/logout")
async def logout():
    """Logout endpoint (token invalidation handled on frontend)"""
    return {"message": "Logged out successfully"}

@app.get("/auth/verify")
async def verify_auth(token: Optional[str] = None):
    """Verify if token is valid"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {"email": email, "valid": True}

# Configuration system for OpenAI & Groq API Keys

class ConfigManager:
    def __init__(self):
        self.openai_api_key = None
        self.grok_api_key = None
        self.use_grok = True  # Default to Groq
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
                        
                        # Set provider (default to groq)
                        self.use_grok = provider == 'groq'
                        print(f"✅ AI Provider set to: {'🦅 GROQ' if self.use_grok else '🤖 OPENAI'} (from config.json)")
                    else:
                        # Legacy config format for backward compatibility
                        if config.get('openai_api_key'):
                            self.openai_api_key = config['openai_api_key']
                            print("✅ OpenAI API Key loaded from config.json")
                        
                        if config.get('grok_api_key'):
                            self.grok_api_key = config['grok_api_key']
                            print("✅ Groq API Key loaded from config.json")
                        
                        if 'use_grok' in config:
                            self.use_grok = config.get('use_grok', True)  # Default to True
                            print(f"✅ AI Provider set to: {'🦅 GROQ' if self.use_grok else '🤖 OPENAI'} (from config.json)")
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
            print(f"✅ AI Provider set to: {'🦅 GROQ' if self.use_grok else '🤖 OPENAI'} (from environment)")
        else:
            # Default to Groq if not specified
            self.use_grok = True
        
        # Print summary
        print(f"\n📊 AI Configuration Summary:")
        print(f"  OpenAI Available: {bool(self.openai_api_key)}")
        print(f"  Groq Available: {bool(self.grok_api_key)}")
        print(f"  Current Provider: {'🦅 GROQ' if self.use_grok else '🤖 OPENAI'}")
        print(f"  Default: GROQ (configurable via AI_PROVIDER env var)")
        
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

# Load models from frontend/public (monorepo structure)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
MODELS_PATH = os.path.join(ROOT_DIR, 'frontend', 'public', 'models.json')

def load_models():
    try:
        with open(MODELS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[INFO] Models file not found at {MODELS_PATH} - using defaults")
        return None

models = load_models()

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    query: str
    session_id: Optional[str] = None  # Conversation session ID

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

def generate_insights(user_query: str, intent: QueryIntent, query_result: QueryResult, session: Optional[ConversationSession] = None) -> str:
    """Generate AI insights using configured provider (OpenAI or Groq) with conversation context"""
    
    # Check if any provider is configured
    if not config_manager.is_configured():
        print("⚠️ No AI providers configured. Using fallback...")
        return generate_expert_fallback_from_query(intent, query_result, session=session, user_query=user_query)
    
    try:
        from data_enrichment import enrich_shipment
        from llm_context import (
            build_shipment_context, build_aggregated_context,
            get_system_prompt_for_intent, generate_guaranteed_insights
        )
        
        # Build LLM context based on query type
        llm_context = None
        system_prompt = session.get_system_prompt() if session else get_system_prompt_for_intent(intent.query_type)
        
        # For single shipment queries, enrich the data
        if intent.query_type == 'shipment_details' and query_result.data:
            try:
                enriched = enrich_shipment(query_result.data[0])
                llm_context = build_shipment_context(enriched)
                # Store in session context
                if session:
                    session.update_context('last_shipment_id', enriched.shipment_id)
                    session.update_context('last_sku', enriched.sku)
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
        
        # Build messages with conversation history
        messages = []
        
        # Add conversation history if available
        if session:
            history = session.get_history(limit=6)  # Last 6 messages for context
            for msg in history:
                messages.append(msg)
        
        # Add system prompt
        messages.insert(0, {
            "role": "system",
            "content": system_prompt
        })
        
        # Add current user query with conciseness enforcement
        # Check if this is a follow-up question (short query to existing context)
        is_followup = len(user_query) < 50 and len(session.messages) > 2 if session else False
        
        if is_followup:
            # For follow-ups, be EXTREMELY concise
            user_content = f"""FOLLOW-UP QUESTION: {user_query}

CRITICAL: This is a follow-up. Do NOT repeat information from previous messages.
Answer with MAXIMUM 1-2 sentences. Be direct.

Data context if needed:
{context_for_llm}"""
        else:
            # For new queries, provide full context
            user_content = f"""Analyze this shipment information and respond according to your professional guidelines:

{context_for_llm}

Customer Query: {user_query}

RESPONSE RULES:
1. Keep answer to 2-3 sentences MAXIMUM
2. Answer only what was asked
3. Use emoji for clarity: 📦=cargo, 📅=date, ⚠️=risk, 🚚=status
4. Format: SHP-ID | SKU (qty) | Route | Status | Risk
5. Never repeat previous context in same conversation
6. Use data-driven insights only"""
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # USE GROQ
        if config_manager.use_grok:
            from ai_providers_groq import call_groq_api
            response = call_groq_api(config_manager.grok_api_key, messages, system_prompt, user_query)
        
        # USE OPENAI
        else:
            from ai_providers_openai import call_openai_api
            response = call_openai_api(config_manager.openai_api_key, messages, user_query)
        
        # Store in session history
        if session:
            session.add_message("user", user_query)
            session.add_message("assistant", response)
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Error: {error_msg}")
        import traceback
        traceback.print_exc()
        # Use fallback for this query
        return generate_expert_fallback_from_query(intent, query_result, session=session, user_query=user_query)


def generate_expert_fallback_from_query(intent: Optional[QueryIntent], query_result: Optional[QueryResult], session: Optional[ConversationSession] = None, user_query: Optional[str] = None) -> str:
    """Generate concise response answering exactly what user asked (no AI service)"""
    
    if intent is None or query_result is None:
        return "⚠️ Service temporarily unavailable."
    
    try:
        # Check if this is a short follow-up question (hint: very short query + existing messages)
        is_followup = user_query and len(user_query) < 50 and session and len(session.messages) > 2
        
        # SHIPMENT DETAILS - Show enriched shipment data
        if intent.query_type == 'shipment_details' and query_result.data:
            try:
                data = query_result.data[0]  # Already enriched from query_engine
                
                # For follow-ups like "source?", "what's the source?", return ONLY the requested info
                if is_followup:
                    query_lower = user_query.lower() if user_query else ""
                    if 'source' in query_lower:
                        source = data.get('source', 'Unknown')
                        return source
                    elif 'destination' in query_lower or 'dest' in query_lower:
                        destination = data.get('destination', 'Unknown')
                        return destination
                    elif 'risk' in query_lower:
                        risk_score = data.get('risk_score', 0)
                        risk_level = 'HIGH' if risk_score > 0.7 else 'MEDIUM' if risk_score > 0.4 else 'LOW'
                        risk_emoji = "🔴" if risk_score > 0.7 else "🟡" if risk_score > 0.4 else "🟢"
                        return f"{risk_emoji} {risk_level}"
                    elif 'sku' in query_lower:
                        sku = data.get('sku', 'Unknown')
                        qty = data.get('quantity', 0)
                        return f"{sku} ({qty} units)"
                    elif 'status' in query_lower:
                        return data.get('status', 'Unknown')
                    elif 'delay' in query_lower:
                        delay_days = data.get('delay_days') or 0
                        return f"{delay_days} days overdue" if delay_days > 0 else "On schedule"
                    elif 'date' in query_lower or 'arrival' in query_lower:
                        return f"Expected: {data.get('expected_arrival')} | Shipped: {data.get('shipped_date')}"
                
                # For full details, provide comprehensive response
                response = f"**{data.get('shipment_id')}** - {data.get('status')}\n"
                
                # Use source/destination if available, otherwise use route
                source = data.get('source', 'Unknown')
                destination = data.get('destination', 'Unknown')
                if source != 'Unknown' and destination != 'Unknown':
                    route_str = f"{source} → {destination}"
                else:
                    route_str = data.get('route', 'Unknown → Unknown')
                
                response += f"📦 {data.get('sku')} ({data.get('quantity')} units) | {route_str}\n"
                response += f"📅 Shipped: {data.get('shipped_date')} | Expected: {data.get('expected_arrival')}\n"
                
                if data.get('actual_arrival'):
                    response += f"✅ Delivered: {data.get('actual_arrival')} ({data.get('transit_days')} days)\n"
                else:
                    delay_days = data.get('delay_days') or 0
                    response += f"⏳ In Transit ({delay_days} days overdue)\n"
                
                risk_score = data.get('risk_score', 0)
                risk_emoji = "🔴" if risk_score > 0.7 else "🟡" if risk_score > 0.4 else "🟢"
                response += f"{risk_emoji} Risk: {'HIGH' if risk_score > 0.7 else 'MEDIUM' if risk_score > 0.4 else 'LOW'}\n"
                
                recommendations = data.get('recommendations', [])
                if recommendations:
                    response += f"\n**Next Steps:**\n"
                    for i, rec in enumerate(recommendations[:1], 1):
                        response += f"{i}. {rec}\n"
                
                return response
            except Exception as e:
                print(f"Error processing shipment data: {e}")
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
    🚀 IMPROVED AI-Powered Supply Chain Copilot
    
    Uses accurate data analysis + optional Groq LLM
    
    Features:
    1. Accurate metrics calculation from CSV data
    2. Intelligent query type detection
    3. Crisp, supply-chain-standard formatting
    4. Zero hallucinations - only real data
    5. Session-aware conversation context
    
    Queries answered:
    - "on time rate?" → Exact % with breakdown
    - "how many sku?" → Exact count + top SKUs
    - "SHP-0000001" → Full shipment details
    - "shipments from UK-LON?" → Count + metrics
    - "best route?" → Top routes by on-time %
    - "critical shipments?" → High-risk items
    """
    user_query = request.query
    
    try:
        print(f"\n🎯 IMPROVED SUPPLY CHAIN QUERY")
        print(f"📥 Query: {user_query}")
        
        # Load CSV data
        df = load_csv()
        if df.empty:
            return {
                "response": "⚠️ Supply chain data not available",
                "session_id": request.session_id or "error",
                "error": "No data",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get or create conversation session
        session = get_or_create_session(request.session_id)
        print(f"📌 Session: {session.session_id}")
        
        # Generate accurate response using improved analyzer
        response_generator = ImprovedResponseGenerator(df)
        response_text, metadata = response_generator.generate_response(user_query)
        
        print(f"✅ Response generated: {metadata['query_type']}")
        print(f"   Confidence: {metadata['confidence']:.0%}")
        
        # Store in session
        session.add_message("user", user_query)
        session.add_message("assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session.session_id,
            "message_count": len(session.messages),
            "query_type": metadata['query_type'],
            "confidence": metadata['confidence'],
            "ai_powered": True,
            "data_source": "CSV (accurate)",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        
        session = get_or_create_session(request.session_id)
        
        return {
            "response": f"⚠️ Error: {str(e)[:100]}",
            "session_id": session.session_id,
            "query_type": "error",
            "confidence": 0.0,
            "ai_powered": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/chat/smart")
async def chat_smart(request: ChatRequest):
    """
    🚀 SMART Query Endpoint - Intelligent Intent Detection + Data-Driven Responses
    
    Uses advanced intent detection and data-driven query execution:
    - Automatically detects aggregation dimension (destination, source, SKU, route)
    - Intelligently interprets sort order (most vs least/fewest)
    - Returns ranked, properly formatted results
    - No manual pattern matching - works with any query structure
    
    Request:
    {
        "query": "which destination has less shipment",
        "session_id": "optional-session-uuid"
    }
    
    Response:
    {
        "response": "Destinations with fewest shipments (top 10): ...",
        "session_id": "uuid",
        "structured_data": {...},
        "timestamp": "..."
    }
    """
    user_query = request.query
    
    try:
        print(f"\n🚀 SMART CHAT: {user_query}")
        
        # Get or create session
        session = get_or_create_session(request.session_id)
        session.add_message("user", user_query)
        
        # Step 1: Parse intent intelligently
        intent = smart_parse_intent(user_query)
        print(f"🧠 Smart Intent: {intent.aggregation.value} | Sort: {intent.sort_order.value} | Limit: {intent.limit}")
        
        # Step 2: Execute smart query
        query_result = execute_smart_query(intent)
        print(f"✅ Query Result: {query_result.get('summary', 'Success')}")
        
        # Step 3: Format response
        response_text = format_for_response(query_result)
        
        # Store in session
        session.add_message("assistant", response_text)
        
        return {
            "response": response_text,
            "session_id": session.session_id,
            "message_count": len(session.messages),
            "smart_query": True,
            "intent": {
                "aggregation": intent.aggregation.value,
                "sort_order": intent.sort_order.value,
                "limit": intent.limit,
                "confidence": intent.confidence
            },
            "structured_data": {
                "summary": query_result.get("summary"),
                "data": query_result.get("data", [])[:10],
                "total_unique": query_result.get("total_unique")
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        print(f"❌ Smart Chat Error: {e}")
        traceback.print_exc()
        
        session = get_or_create_session(request.session_id)
        
        return {
            "response": f"⚠️ Error: {str(e)}",
            "session_id": session.session_id,
            "smart_query": True,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = sessions[session_id]
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "message_count": len(session.messages),
        "messages": session.get_history(limit=50),  # Return last 50 messages
        "context": session.context,
        "ai_powered": True
    }

@app.post("/session/new")
async def create_new_session():
    """Create a new conversation session"""
    session = get_or_create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "message": "New session created. Use this session_id in future /chat requests to maintain conversation context."
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    del sessions[session_id]
    return {
        "message": f"Session {session_id} deleted",
        "remaining_sessions": len(sessions)
    }

@app.get("/sessions")
async def list_sessions():
    """List all active sessions (admin endpoint)"""
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "message_count": len(s.messages)
            }
            for s in sessions.values()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Load models from frontend/public (monorepo structure)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
MODELS_PATH = os.path.join(ROOT_DIR, 'frontend', 'public', 'models.json')

def load_models():
    try:
        with open(MODELS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[INFO] Models file not found at {MODELS_PATH} - using defaults")
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
