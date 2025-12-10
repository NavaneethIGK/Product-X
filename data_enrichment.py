"""
DATA PREPARATION & ENRICHMENT LAYER
Transforms raw CSV data into structured, meaningful insights
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

class ShipmentSummary:
    """Structured shipment JSON - never expose raw CSV"""
    def __init__(self, shipment_id: str, sku: str, quantity: int, source: str, destination: str, 
                 route: str, shipped_date: str, expected_arrival: str, actual_arrival: Optional[str],
                 status_label: str, transit_days: Optional[int], expected_transit_days: int,
                 delay_days: Optional[int], risk_score: float, shipment_health: str,
                 estimated_delay_reason: Optional[str], eta_forecast: Optional[str],
                 status_interpretation: str, timeline_summary: str, recommendations: List[str],
                 raw_status: str):
        self.shipment_id = shipment_id
        self.sku = sku
        self.quantity = quantity
        self.source = source
        self.destination = destination
        self.route = route
        self.shipped_date = shipped_date
        self.expected_arrival = expected_arrival
        self.actual_arrival = actual_arrival
        self.status_label = status_label
        self.transit_days = transit_days
        self.expected_transit_days = expected_transit_days
        self.delay_days = delay_days
        self.risk_score = risk_score
        self.shipment_health = shipment_health
        self.estimated_delay_reason = estimated_delay_reason
        self.eta_forecast = eta_forecast
        self.status_interpretation = status_interpretation
        self.timeline_summary = timeline_summary
        self.recommendations = recommendations
        self.raw_status = raw_status
    
    @property
    def shipped_date_short(self) -> str:
        """Return short formatted date (e.g., Oct 26, 2025)"""
        try:
            dt = pd.to_datetime(self.shipped_date)
            return dt.strftime('%b %d, %Y')
        except:
            return self.shipped_date
    
    @property
    def expected_arrival_short(self) -> str:
        """Return short formatted date (e.g., Nov 08, 2025)"""
        try:
            dt = pd.to_datetime(self.expected_arrival)
            return dt.strftime('%b %d, %Y')
        except:
            return self.expected_arrival
    
    @property
    def actual_arrival_short(self) -> Optional[str]:
        """Return short formatted date or None"""
        if not self.actual_arrival:
            return None
        try:
            dt = pd.to_datetime(self.actual_arrival)
            return dt.strftime('%b %d, %Y')
        except:
            return self.actual_arrival


def normalize_date(date_value) -> Optional[str]:
    """Convert any date to ISO format string or None"""
    if pd.isna(date_value) or date_value is None:
        return None
    try:
        dt = pd.to_datetime(date_value)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None


def calculate_transit_days(shipped: Optional[str], arrived: Optional[str]) -> Optional[int]:
    """Calculate actual transit days"""
    if not shipped or not arrived:
        return None
    try:
        ship_dt = pd.to_datetime(shipped)
        arrival_dt = pd.to_datetime(arrived)
        return (arrival_dt - ship_dt).days
    except:
        return None


def calculate_expected_transit_days(shipped: Optional[str], expected: Optional[str]) -> int:
    """Calculate planned transit days"""
    if not shipped or not expected:
        return 0
    try:
        ship_dt = pd.to_datetime(shipped)
        expected_dt = pd.to_datetime(expected)
        days = (expected_dt - ship_dt).days
        return max(1, days)  # At least 1 day
    except:
        return 0


def calculate_delay_days(expected: Optional[str], arrived: Optional[str]) -> Optional[int]:
    """Calculate delay in days (positive = late, negative = early, None = not arrived)"""
    if not expected or not arrived:
        return None
    try:
        expected_dt = pd.to_datetime(expected)
        arrival_dt = pd.to_datetime(arrived)
        delay = (arrival_dt - expected_dt).days
        return delay if delay > 0 else 0  # Only count positive delays
    except:
        return None


def determine_status_label(raw_status: str, delay_days: Optional[int], arrived: Optional[str], expected: Optional[str]) -> str:
    """Convert raw status to human-friendly label"""
    if raw_status is None:
        return "Unknown"
    
    raw_status_clean = str(raw_status).strip().upper()
    
    # If arrived
    if arrived and raw_status_clean in ['ARRIVED', 'DELIVERED', 'COMPLETED']:
        if delay_days is None or delay_days <= 0:
            return "Delivered On Time ✓"
        else:
            return f"Delivered Late (by {delay_days} days)"
    
    # If in transit
    if raw_status_clean in ['IN_TRANSIT', 'IN TRANSIT', 'SHIPPED', 'DISPATCHED', 'IN_PROGRESS']:
        # Check if overdue
        if expected:
            expected_dt = pd.to_datetime(expected, errors='coerce')
            if pd.notna(expected_dt) and expected_dt < datetime.now():
                return "⚠ In Transit & Overdue"
        return "In Transit"
    
    # Pending/Waiting
    if raw_status_clean in ['PENDING', 'WAITING', 'PROCESSING', 'PREPARING']:
        return "Pending Processing"
    
    # Other statuses
    return f"Status: {raw_status_clean}"


def estimate_delay_reason(expected: Optional[str], arrived: Optional[str], delay_days: Optional[int], 
                         source: str, destination: str) -> Optional[str]:
    """Estimate why shipment might be delayed"""
    if delay_days is None or delay_days <= 0:
        return None
    
    reasons = []
    
    # Delay severity
    if delay_days > 10:
        reasons.append("Extended delay detected")
    elif delay_days > 5:
        reasons.append("Moderate delay")
    
    # Route analysis
    if source and destination:
        # Long routes are more prone to delays
        if source != destination:
            reasons.append("Complex routing may have contributed")
    
    # Time-based reasons (heuristic)
    if arrived:
        arrival_dt = pd.to_datetime(arrived, errors='coerce')
        if pd.notna(arrival_dt):
            # Weekend deliveries might be affected
            if arrival_dt.weekday() >= 5:  # Saturday/Sunday
                reasons.append("Possible weekend processing delays")
    
    return " | ".join(reasons) if reasons else "Delay reason unclear from data"


def forecast_eta(expected: Optional[str], arrived: Optional[str], raw_status: str) -> Optional[str]:
    """Forecast ETA for in-transit shipments"""
    if arrived or not expected:
        return None
    
    raw_status_clean = str(raw_status).strip().upper()
    if raw_status_clean not in ['IN_TRANSIT', 'IN TRANSIT', 'SHIPPED', 'DISPATCHED']:
        return None
    
    try:
        expected_dt = pd.to_datetime(expected, errors='coerce')
        if pd.isna(expected_dt):
            return None
        
        now = datetime.now()
        
        # If already past expected date, it's likely delayed
        if expected_dt < now:
            days_overdue = (now - expected_dt).days
            return f"Expected on {expected_dt.strftime('%Y-%m-%d')} ({days_overdue} days overdue)"
        
        # If approaching
        days_until = (expected_dt - now).days
        if days_until == 0:
            return f"Expected today: {expected_dt.strftime('%Y-%m-%d')}"
        elif days_until == 1:
            return f"Expected tomorrow: {expected_dt.strftime('%Y-%m-%d')}"
        else:
            return f"Expected in {days_until} days: {expected_dt.strftime('%Y-%m-%d')}"
    except:
        return None


def calculate_risk_score(delay_days: Optional[int], expected: Optional[str], 
                        arrived: Optional[str], raw_status: str) -> float:
    """Calculate risk score 0.0-1.0 (higher = more risk)"""
    score = 0.0
    
    # No arrival yet
    if not arrived:
        if expected:
            expected_dt = pd.to_datetime(expected, errors='coerce')
            if pd.notna(expected_dt) and expected_dt < datetime.now():
                score += 0.7  # Overdue and not arrived = high risk
            else:
                score += 0.2  # Not yet due, low risk
        else:
            score += 0.3  # Unknown expected, moderate risk
    
    # Already delayed
    if delay_days and delay_days > 0:
        if delay_days >= 10:
            score += 0.5  # Major delay
        elif delay_days >= 5:
            score += 0.3  # Moderate delay
        else:
            score += 0.1  # Minor delay
    
    return min(1.0, score)


def determine_shipment_health(risk_score: float, delay_days: Optional[int], raw_status: str) -> str:
    """Determine overall shipment health"""
    raw_status_clean = str(raw_status).strip().upper()
    
    # Delivered on time
    if raw_status_clean in ['ARRIVED', 'DELIVERED', 'COMPLETED']:
        if delay_days is None or delay_days <= 0:
            return "Excellent ✓"
        elif delay_days <= 3:
            return "Good"
        else:
            return "Late"
    
    # In transit assessment
    if raw_status_clean in ['IN_TRANSIT', 'IN TRANSIT', 'SHIPPED', 'DISPATCHED']:
        if risk_score > 0.6:
            return "At Risk ⚠"
        elif risk_score > 0.3:
            return "Caution"
        else:
            return "Good"
    
    # Pending/processing
    return "In Progress"


def create_status_interpretation(status_label: str, delay_days: Optional[int], 
                                 expected: Optional[str], actual: Optional[str],
                                 raw_status: str) -> str:
    """Create human-friendly status interpretation"""
    raw_status_clean = str(raw_status).strip().upper()
    
    if raw_status_clean in ['ARRIVED', 'DELIVERED', 'COMPLETED']:
        if delay_days is None or delay_days <= 0:
            return "✓ Shipment delivered on time and ready for pickup/use."
        else:
            return f"⚠ Shipment delivered {delay_days} days late. You may want to review carrier performance."
    
    elif raw_status_clean in ['IN_TRANSIT', 'IN TRANSIT', 'SHIPPED', 'DISPATCHED']:
        if expected:
            expected_dt = pd.to_datetime(expected, errors='coerce')
            if pd.notna(expected_dt):
                days_until = (expected_dt - datetime.now()).days
                if days_until > 0:
                    return f"Your shipment is currently in transit and on schedule. Expected arrival in {days_until} days."
                else:
                    return f"Your shipment is in transit but has exceeded the expected delivery date by {abs(days_until)} days. Please contact support if it hasn't arrived soon."
        return "Your shipment is actively moving through the supply chain."
    
    elif raw_status_clean in ['PENDING', 'WAITING', 'PROCESSING', 'PREPARING']:
        return "Your shipment is being prepared and will be dispatched shortly."
    
    else:
        return f"Current status: {status_label}. Please check tracking details."


def create_timeline_summary(shipped: Optional[str], expected: Optional[str], 
                           actual: Optional[str], transit_days: Optional[int],
                           expected_transit_days: int) -> str:
    """Create timeline interpretation"""
    parts = []
    
    if shipped:
        ship_dt = pd.to_datetime(shipped, errors='coerce')
        if pd.notna(ship_dt):
            parts.append(f"Shipped on {ship_dt.strftime('%B %d, %Y')}")
    
    if expected:
        exp_dt = pd.to_datetime(expected, errors='coerce')
        if pd.notna(exp_dt):
            parts.append(f"Expected arrival {exp_dt.strftime('%B %d, %Y')} ({expected_transit_days} days planned)")
    
    if actual:
        act_dt = pd.to_datetime(actual, errors='coerce')
        if pd.notna(act_dt):
            parts.append(f"Actually arrived {act_dt.strftime('%B %d, %Y')}")
            if transit_days:
                parts.append(f"(took {transit_days} days)")
    
    return " → ".join(parts) if parts else "Timeline information unavailable"


def generate_recommendations(status_label: str, risk_score: float, delay_days: Optional[int],
                            expected: Optional[str], raw_status: str) -> List[str]:
    """Generate actionable recommendations"""
    recommendations = []
    
    raw_status_clean = str(raw_status).strip().upper()
    
    # For delayed shipments
    if delay_days and delay_days > 0:
        recommendations.append("Contact carrier to understand delay reasons")
        if delay_days >= 7:
            recommendations.append("Consider filing a claim if delay impacts business")
    
    # For overdue in-transit
    if raw_status_clean in ['IN_TRANSIT', 'IN TRANSIT'] and expected:
        expected_dt = pd.to_datetime(expected, errors='coerce')
        if pd.notna(expected_dt) and expected_dt < datetime.now():
            recommendations.append("Follow up with logistics provider regarding delayed delivery")
    
    # For high-risk shipments
    if risk_score > 0.6:
        recommendations.append("Monitor shipment closely and prepare contingency plans")
    
    # For pending
    if raw_status_clean in ['PENDING', 'WAITING', 'PROCESSING']:
        recommendations.append("Check back soon for shipping updates")
    
    # For delivered on time
    if "on time" in status_label.lower() and "delivered" in status_label.lower():
        recommendations.append("Schedule pickup or arrange delivery at your convenience")
    
    if not recommendations:
        recommendations.append("Continue tracking for status updates")
    
    return recommendations


def enrich_shipment(row: Dict[str, Any]) -> ShipmentSummary:
    """Transform raw CSV row into enriched shipment summary"""
    
    # Extract and normalize raw fields
    shipment_id = str(row.get('shipment_id', 'UNKNOWN')).strip()
    sku = str(row.get('sku', 'UNKNOWN')).strip()
    quantity = int(row.get('quantity', 0))
    source = str(row.get('source', row.get('source_location', 'Unknown'))).strip()
    destination = str(row.get('destination', row.get('destination_location', 'Unknown'))).strip()
    route = str(row.get('route', f"{source} → {destination}")).strip()
    raw_status = str(row.get('status', 'UNKNOWN')).strip()
    
    # Normalize dates
    shipped_date = normalize_date(row.get('shipped_date', row.get('departed_at')))
    expected_arrival = normalize_date(row.get('expected_arrival'))
    actual_arrival = normalize_date(row.get('arrived_at'))
    
    # Calculate derived values
    transit_days = calculate_transit_days(shipped_date, actual_arrival)
    expected_transit_days = calculate_expected_transit_days(shipped_date, expected_arrival)
    delay_days = calculate_delay_days(expected_arrival, actual_arrival)
    
    # Generate insights
    status_label = determine_status_label(raw_status, delay_days, actual_arrival, expected_arrival)
    delay_reason = estimate_delay_reason(expected_arrival, actual_arrival, delay_days, source, destination)
    eta_forecast = forecast_eta(expected_arrival, actual_arrival, raw_status)
    risk_score = calculate_risk_score(delay_days, expected_arrival, actual_arrival, raw_status)
    shipment_health = determine_shipment_health(risk_score, delay_days, raw_status)
    status_interpretation = create_status_interpretation(status_label, delay_days, expected_arrival, actual_arrival, raw_status)
    timeline_summary = create_timeline_summary(shipped_date, expected_arrival, actual_arrival, transit_days, expected_transit_days)
    recommendations = generate_recommendations(status_label, risk_score, delay_days, expected_arrival, raw_status)
    
    return ShipmentSummary(
        shipment_id=shipment_id,
        sku=sku,
        quantity=quantity,
        source=source,
        destination=destination,
        route=route,
        shipped_date=shipped_date or "Unknown",
        expected_arrival=expected_arrival or "Unknown",
        actual_arrival=actual_arrival,
        status_label=status_label,
        transit_days=transit_days,
        expected_transit_days=expected_transit_days,
        delay_days=delay_days,
        risk_score=round(risk_score, 2),
        shipment_health=shipment_health,
        estimated_delay_reason=delay_reason,
        eta_forecast=eta_forecast,
        status_interpretation=status_interpretation,
        timeline_summary=timeline_summary,
        recommendations=recommendations,
        raw_status=raw_status
    )


def enrich_dataframe(df: pd.DataFrame) -> List[ShipmentSummary]:
    """Enrich entire dataframe"""
    enriched = []
    for _, row in df.iterrows():
        enriched.append(enrich_shipment(row.to_dict()))
    return enriched


def build_llm_context(enriched_shipment: ShipmentSummary) -> str:
    """
    Build complete, professional context for LLM
    LLM receives ONLY clean, structured data - never raw CSV
    """
    
    context = f"""
SHIPMENT INTELLIGENCE CONTEXT
=============================

SHIPMENT IDENTIFICATION:
- Shipment ID: {enriched_shipment.shipment_id}
- SKU Code: {enriched_shipment.sku}
- Quantity: {enriched_shipment.quantity} units
- Route: {enriched_shipment.source} → {enriched_shipment.destination}

TIMELINE DATA:
- Departure: {enriched_shipment.shipped_date}
- Expected Arrival: {enriched_shipment.expected_arrival}
- Actual Arrival: {enriched_shipment.actual_arrival or '(Still in transit - not yet delivered)'}
- Expected Transit Duration: {enriched_shipment.expected_transit_days} days
- Actual Transit Duration: {enriched_shipment.transit_days or '(In progress)'}
- Delay Status: {enriched_shipment.delay_days or 0} days

OPERATIONAL CLASSIFICATION:
- Current Status: {enriched_shipment.status_label}
- Shipment Health: {enriched_shipment.shipment_health}
- Risk Level: {_risk_level_label(enriched_shipment.risk_score)}
- ETA Forecast: {enriched_shipment.eta_forecast or 'Already delivered'}

ENRICHED INSIGHTS:
- Status Interpretation: {enriched_shipment.status_interpretation}
- Timeline Summary: {enriched_shipment.timeline_summary}
- Estimated Delay Reason: {enriched_shipment.estimated_delay_reason or 'No delays detected'}
- Recommended Actions: {', '.join(enriched_shipment.recommendations)}

DATA QUALITY:
All fields have been normalized, validated, and enriched. Ready for expert analysis.
"""
    
    return context


def _risk_level_label(risk_score: float) -> str:
    """Convert risk score to label"""
    if risk_score >= 0.7:
        return "HIGH RISK ⚠️"
    elif risk_score >= 0.4:
        return "MEDIUM RISK ⚡"
    else:
        return "LOW RISK ✓"


def get_system_prompt() -> str:
    """
    PROFESSIONAL LLM SYSTEM PROMPT
    Forces expert-level, customer-centric responses
    """
    return """You are a highly professional, expert-level Supply Chain & Logistics AI Assistant.

Your role is to analyze shipment data and provide customers with clear, actionable insights about their orders.

CORE PRINCIPLES:
- You MUST interpret data like a senior logistics expert
- You MUST provide rich, human-friendly explanations
- You MUST predict shipment status with confidence
- You MUST explain risk and estimated timelines
- You MUST offer proactive guidance and next steps
- You MUST maintain a confident, professional, customer-success tone
- You MUST NEVER say "I don't know" or "data not available"
- When data is incomplete, use reasonable industry assumptions
- Transform basic CSV fields into meaningful, expert explanations

MANDATORY OUTPUT STRUCTURE FOR EVERY RESPONSE:

1. **STATUS SUMMARY**
   - Provide a crisp professional summary
   - Interpret the shipment status (not just restate it)
   - Mention source → destination route
   - Confirm if the shipment is progressing normally

2. **TIMELINE ANALYSIS**
   - Report dates: shipped, expected arrival, actual arrival (if available)
   - Calculate and state transit days
   - Calculate and state delay days (if any)
   - Clearly state if shipment is early, on-time, or delayed

3. **ETA & DELAY INTERPRETATION**
   - If arrived: Confirm arrival status and any delays
   - If in-transit: Compare today vs expected_arrival date
   - Predict if on track or at risk of delay
   - Explain the situation in plain language

4. **CARGO DETAILS**
   - Explain SKU and quantity in customer-friendly language
   - Note any relevant context about the cargo

5. **RISK EVALUATION**
   - Assign: Low / Medium / High risk
   - Explain the reasoning based on delays, status, and timeline
   - Be specific and data-driven

6. **RECOMMENDATIONS & NEXT STEPS**
   - If delayed: Clear steps to follow
   - If on-time: Reassurance and expected delivery confirmation
   - If in-transit: Clear next movement expectations
   - Always provide actionable guidance

TONE & STYLE:
- Write like a senior logistics manager speaking to a valued customer
- Professional, confident, clear, and genuinely helpful
- Use specific dates and numbers
- Avoid jargon unless necessary
- Always be proactive and solution-oriented

HANDLING INCOMPLETE DATA:
- If dates are missing: Make reasonable assumptions based on industry standards
- If status unclear: Use delay information and timeline to infer
- Never placeholder: Always provide best-possible inference
- Add brief note: "Based on the available information..."

Your goal: Transform raw shipment fields into a rich, insightful, expert-level response that makes the customer feel confident and informed.
"""