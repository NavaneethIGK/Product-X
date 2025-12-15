"""
CONTEXT SHAPING LAYER FOR LLM
Prepares cleaned, enriched data for language model consumption
Includes system prompts and context formatting
"""
from typing import Dict, Any, List, Optional
from data_enrichment import ShipmentSummary, build_llm_context, get_system_prompt
import json

# ============================================================================
# PROFESSIONAL SYSTEM PROMPT - Primary directive for LLM
# ============================================================================

SYSTEM_PROMPT_PROFESSIONAL = get_system_prompt()

# Legacy system prompts for specific intents
SYSTEM_PROMPT_SHIPMENT_EXPERT = """You are an expert supply chain logistics analyst. Your role is to provide clear, actionable insights about shipments to business users and customers.

TONE & STYLE:
- Professional yet approachable
- Data-driven and specific
- Focused on customer impact
- Solution-oriented

RESPONSE STRUCTURE (always follow this):
1. **Status Summary** - Clear one-liner about the shipment state
2. **Timeline Interpretation** - What happened, when, what's next
3. **Risk Assessment** - If any delays or concerns exist
4. **ETA & Expectations** - When it will arrive or when it should have arrived
5. **Recommendations** - Specific actions the user should take
6. **SKU & Quantity Confirmation** - What's being shipped

CRITICAL RULES:
- NEVER expose raw CSV data
- ALWAYS use the enriched "shipment_health" score to assess situation
- ALWAYS explain delays in human terms (not just numbers)
- ALWAYS provide next steps, even if data is incomplete
- If a field is missing, provide best-guess explanation based on what you DO have
- Be proactive: identify potential issues before user asks
- Use risk_score (0.0-1.0) to prioritize concerns

FACTS YOU HAVE:
- Shipment ID, SKU, quantity, route
- Actual vs expected timeline
- Current status label
- Calculated delay days
- Risk score and health status
- Estimated delay reasons

TONE EXAMPLES:
- On-time delivery: "Excellent news! Your shipment arrived as promised on [date]."
- Delayed: "Your shipment experienced a [reason] and arrived [days] days later than expected. Here's what you should do..."
- In transit overdue: "Your shipment is running late. We recommend contacting the carrier immediately to track progress."
- In processing: "Your order is being prepared and will ship within [timeframe]."

Remember: The user wants confidence and clarity. Explain what this means for THEM, not just what the data says."""

SYSTEM_PROMPT_ANALYST = """You are a supply chain analyst helping business teams understand logistics performance.

ANALYSIS FOCUS:
- Performance trends (on-time, delays, risk patterns)
- Cost implications of delays
- Recommendations for process improvement
- Risk assessment and mitigation

ALWAYS:
1. Summarize key metrics clearly
2. Highlight risk areas
3. Provide actionable improvements
4. Use risk_score to prioritize issues
5. Reference specific data points

NEVER:
- Expose raw CSV rows
- Make vague statements
- Miss obvious risks
- Forget about cost/business impact"""

SYSTEM_PROMPT_TRACKER = """You are a shipment tracking assistant. Users want to know where their shipment is and when it will arrive.

KEY QUESTIONS YOU ANSWER:
- Where is my shipment right now?
- When will it arrive?
- Is it delayed?
- What should I do?

FORMAT YOUR RESPONSE:
1. **Current Status**: One clear sentence
2. **Location & Timeline**: Where it is, when it shipped, when it arrives/arrived
3. **If Delayed**: Why, by how long, impact
4. **If On-Time**: Great! Here's what's next
5. **Action Items**: What the user should do

TONE: Friendly, clear, reassuring (even if there's a problem)
GOAL: User leaves the conversation knowing exactly where they stand"""

# ============================================================================
# CONTEXT BUILDERS
# ============================================================================

def build_shipment_context(enriched: ShipmentSummary) -> Dict[str, Any]:
    """Build complete context for shipment queries
    
    Returns structured, professional context for LLM consumption.
    NEVER exposes raw CSV - only enriched, validated data.
    Includes full LLM context string for direct model input.
    """
    
    context_dict = {
        "shipment_id": enriched.shipment_id,
        "order_details": {
            "sku": enriched.sku,
            "quantity": enriched.quantity,
            "route": enriched.route,
            "source": enriched.source,
            "destination": enriched.destination,
        },
        "timeline": {
            "shipped": enriched.shipped_date,
            "expected_arrival": enriched.expected_arrival,
            "actual_arrival": enriched.actual_arrival,
            "expected_transit_days": enriched.expected_transit_days,
            "actual_transit_days": enriched.transit_days,
        },
        "status": {
            "current": enriched.status_label,
            "interpretation": enriched.status_interpretation,
            "health": enriched.shipment_health,
            "raw_status": enriched.raw_status,
        },
        "performance": {
            "delay_days": enriched.delay_days or 0,
            "risk_score": enriched.risk_score,
            "risk_level": _get_risk_level(enriched.risk_score),
            "eta_forecast": enriched.eta_forecast,
            "estimated_delay_reason": enriched.estimated_delay_reason,
        },
        "insights": {
            "timeline_summary": enriched.timeline_summary,
            "recommendations": enriched.recommendations,
        },
        # Full LLM context string for direct model input
        "llm_context": build_llm_context(enriched),
    }
    
    return context_dict


def _get_risk_level(risk_score: float) -> str:
    """Convert numeric risk score to human label"""
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def build_aggregated_context(enriched_list: List[ShipmentSummary], query_type: str) -> Dict[str, Any]:
    """Build context for aggregate queries (multiple shipments)"""
    
    total = len(enriched_list)
    
    # Health distribution
    health_counts = {}
    for e in enriched_list:
        health_counts[e.shipment_health] = health_counts.get(e.shipment_health, 0) + 1
    
    # Risk analysis
    high_risk = [e for e in enriched_list if e.risk_score > 0.6]
    delayed = [e for e in enriched_list if e.delay_days and e.delay_days > 0]
    
    # Average metrics
    avg_risk = sum(e.risk_score for e in enriched_list) / total if total > 0 else 0
    avg_delay = sum(e.delay_days or 0 for e in enriched_list) / total if total > 0 else 0
    
    return {
        "query_type": query_type,
        "total_shipments": total,
        "health_distribution": health_counts,
        "risk_analysis": {
            "average_risk_score": round(avg_risk, 2),
            "high_risk_count": len(high_risk),
            "high_risk_shipments": [e.shipment_id for e in high_risk[:10]],
        },
        "delay_analysis": {
            "delayed_count": len(delayed),
            "average_delay_days": round(avg_delay, 1),
            "most_delayed": sorted(enriched_list, key=lambda e: e.delay_days or 0, reverse=True)[:5],
        },
        "shipments_sample": [
            build_shipment_context(e) for e in enriched_list[:5]
        ]
    }


def format_for_llm(context: Dict[str, Any], system_prompt: str) -> str:
    """Format context as LLM-friendly text"""
    
    formatted = f"""SYSTEM PROMPT:
{system_prompt}

SHIPMENT CONTEXT (JSON):
{json.dumps(context, indent=2)}

INSTRUCTIONS:
1. Use ONLY the data provided above
2. Never ask for missing data - explain what you CAN conclude
3. Follow the response structure from the system prompt
4. Be specific and actionable
5. Explain data in human terms, not raw values"""
    
    return formatted


def create_llm_payload(context: Dict[str, Any], user_query: str, system_prompt: str) -> Dict[str, Any]:
    """Create OpenAI API payload with proper context shaping"""
    
    return {
        "system_prompt": system_prompt,
        "user_query": user_query,
        "context": context,
        "payload": {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"""Based on this shipment context:

{json.dumps(context, indent=2)}

User's question: {user_query}

Provide a clear, actionable response following the structure outlined in your system prompt."""
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
    }


# ============================================================================
# INTENT-SPECIFIC SYSTEM PROMPTS
# ============================================================================

INTENT_SYSTEM_PROMPTS = {
    "shipment_details": SYSTEM_PROMPT_TRACKER,
    "delayed_shipments": SYSTEM_PROMPT_ANALYST,
    "sku_delay_analysis": SYSTEM_PROMPT_ANALYST,
    "route_delay_analysis": SYSTEM_PROMPT_ANALYST,
    "track_shipment": SYSTEM_PROMPT_TRACKER,
    "shipment_status": SYSTEM_PROMPT_TRACKER,
    "orders_by_destination": SYSTEM_PROMPT_ANALYST,
    "orders_by_source": SYSTEM_PROMPT_ANALYST,
    "summary_stats": SYSTEM_PROMPT_ANALYST,
}


def get_system_prompt_for_intent(intent_type: str) -> str:
    """Get the appropriate system prompt for an intent
    
    Always uses the professional Supply Chain & Logistics system prompt
    which enforces expert-level, customer-centric responses
    """
    return SYSTEM_PROMPT_PROFESSIONAL


# ============================================================================
# GUARANTEED INSIGHT GENERATION (even with missing data)
# ============================================================================

def generate_guaranteed_insights(context: Dict[str, Any]) -> List[str]:
    """Generate insights EVEN if some fields are missing - never return empty"""
    
    insights = []
    
    # From status
    if "status" in context and "health" in context["status"]:
        health = context["status"]["health"]
        if "risk" in health.lower():
            insights.append(f"⚠ This shipment is flagged as at-risk ({health})")
        elif "excellent" in health.lower():
            insights.append(f"✓ Shipment health is excellent - no issues detected")
    
    # From risk score
    if "performance" in context and "risk_score" in context["performance"]:
        risk = context["performance"]["risk_score"]
        if risk > 0.7:
            insights.append(f"High risk detected (score: {risk}). Immediate action recommended.")
        elif risk > 0.4:
            insights.append(f"Moderate risk detected. Monitor closely.")
        else:
            insights.append(f"Low risk. Shipment progressing normally.")
    
    # From delay
    if "performance" in context and context["performance"].get("delay_days"):
        delay = context["performance"]["delay_days"]
        if delay > 0:
            insights.append(f"Shipment is delayed by {delay} days.")
            if delay > 7:
                insights.append("This is a significant delay. Consider escalating.")
    
    # From timeline
    if "timeline" in context and "interpretation" in context.get("status", {}):
        insights.append(context["status"]["interpretation"])
    
    # Recommendations
    if "insights" in context and "recommendations" in context["insights"]:
        for rec in context["insights"]["recommendations"][:3]:
            insights.append(f"→ {rec}")
    
    # Fallback if nothing else works
    if not insights:
        insights.append("Shipment data available. See details below.")
    
    return insights
