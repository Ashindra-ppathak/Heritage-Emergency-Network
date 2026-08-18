"""
Report analyzer: extracts a structured evidence summary from a citizen report,
combining simple keyword-based rule analysis with optional Ollama assistance.
"""

from utils.helpers import load_json
from ai.ollama_client import is_ollama_available, generate_risk_reasoning

RISK_RULES = load_json("risk_rules.json")

URGENCY_KEYWORDS = ["urgent", "immediately", "collapse", "collapsing", "fire", "critical", "emergency"]


def detect_keywords(description: str) -> list:
    if not description:
        return []
    text = description.lower()
    found = []
    for kw in list(RISK_RULES.get("keyword_boosts", {}).keys()) + list(
        RISK_RULES.get("intangible_keyword_boosts", {}).keys()
    ):
        if kw in text:
            found.append(kw)
    return found


def detect_urgency(description: str) -> str:
    if not description:
        return "Normal"
    text = description.lower()
    if any(kw in text for kw in URGENCY_KEYWORDS):
        return "Urgent"
    return "Normal"


def recommended_next_action(issue_type: str) -> str:
    """Simple lookup used before full risk scoring is available."""
    mapping = {
        "Structural Damage": "Urgent conservation inspection",
        "Water Damage": "Inspect for moisture ingress and drainage issues",
        "Fire Damage": "Immediate structural safety assessment",
        "Vandalism": "Request site inspection and document damage",
        "Illegal Construction": "Alert local administration for encroachment review",
        "Encroachment": "Alert local administration for encroachment review",
        "Neglect": "Schedule local heritage inspection",
        "Pollution": "Engage environmental/municipal authority",
        "Natural Disaster": "Immediate structural safety assessment",
        "Theft": "Report to authorities and document missing elements",
        "Abandonment": "Schedule site condition inspection",
        "Tradition at Risk": "Engage cultural organization and document practice",
        "Craft Decline": "Engage cultural organization and document active practitioners",
        "Other": "Schedule preliminary review",
    }
    return mapping.get(issue_type, "Schedule preliminary review")


def analyze(description: str, issue_type: str, heritage_type: str, use_ai: bool = True) -> dict:
    """
    Returns a structured evidence summary:
      - detected_keywords
      - urgency
      - evidence_summary
      - recommended_next_action
    """
    keywords = detect_keywords(description)
    urgency = detect_urgency(description)
    action = recommended_next_action(issue_type)

    evidence_summary = (
        f"Report concerns a {heritage_type.lower()} with a reported '{issue_type}' issue. "
    )
    if keywords:
        evidence_summary += f"Notable terms detected: {', '.join(keywords[:5])}. "
    evidence_summary += f"Urgency signal: {urgency}."

    ai_reasoning = ""
    if use_ai and is_ollama_available() and description:
        summary_input = f"{heritage_type} | {issue_type} | {description}"
        ai_reasoning = generate_risk_reasoning(summary_input)

    return {
        "detected_keywords": keywords,
        "urgency": urgency,
        "evidence_summary": evidence_summary,
        "recommended_next_action": action,
        "ai_reasoning": ai_reasoning,
    }
