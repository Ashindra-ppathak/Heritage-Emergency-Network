"""
Risk assessment engine for Heritage Emergency Network.

Combines:
  1. Local Ollama (Phi-3) analysis when available.
  2. A deterministic, rule-based fallback engine that ALWAYS works,
     so the prototype never depends on an external/optional service.

Public function: assess_risk(...) -> dict
"""

from utils.helpers import load_json, risk_level_from_score
from ai.ollama_client import is_ollama_available, analyze_report

RISK_RULES = load_json("risk_rules.json")


def _clamp(score: int) -> int:
    return max(0, min(100, int(score)))


def _keyword_hits(description: str, keyword_map: dict) -> list:
    """Return list of (keyword, boost) that appear in the description."""
    if not description:
        return []
    text = description.lower()
    hits = []
    for kw, boost in keyword_map.items():
        if kw in text:
            hits.append((kw, boost))
    return hits


def fallback_assessment(
    issue_type: str,
    heritage_type: str,
    description: str,
    severity: str,
    is_repeated: bool = False,
) -> dict:
    """
    Deterministic rule-based risk scoring.
    This is the guaranteed path used whenever Ollama is unavailable,
    and also used to sanity-check / support AI output.
    """
    base = RISK_RULES.get("base_risk_by_issue", {}).get(issue_type, 10)
    htype_mod = RISK_RULES.get("heritage_type_modifier", {}).get(heritage_type, 5)
    sev_mod = RISK_RULES.get("severity_modifier", {}).get(severity, 0)

    score = base + htype_mod + sev_mod
    reasons = [f"Issue type '{issue_type}' carries a base risk weighting"]
    if htype_mod:
        reasons.append(f"Heritage type '{heritage_type}' increases sensitivity")
    if sev_mod:
        reasons.append(f"Reporter-observed severity '{severity}' factored in")

    kw_hits = _keyword_hits(description, RISK_RULES.get("keyword_boosts", {}))
    for kw, boost in kw_hits:
        score += boost
        reasons.append(f"Description contains risk keyword: '{kw}'")

    intangible_hits = _keyword_hits(description, RISK_RULES.get("intangible_keyword_boosts", {}))
    for kw, boost in intangible_hits:
        score += boost
        reasons.append(f"Intangible-heritage risk factor detected: '{kw}'")

    if is_repeated:
        bonus = RISK_RULES.get("repeated_report_bonus", 10)
        score += bonus
        reasons.append("Multiple reports received for this site (repeated report bonus)")

    score = _clamp(score)
    level = risk_level_from_score(score)

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
        "source": "fallback",
        "category": issue_type,
        "recommended_priority": _priority_for_level(level),
    }


def _priority_for_level(level: str) -> str:
    mapping = {
        "LOW": "Routine monitoring",
        "MEDIUM": "Scheduled inspection recommended",
        "HIGH": "Priority inspection recommended",
        "CRITICAL": "Urgent expert inspection recommended",
    }
    return mapping.get(level, "Review recommended")


def assess_risk(
    issue_type: str,
    heritage_type: str,
    description: str,
    severity: str,
    is_repeated: bool = False,
    use_ai: bool = True,
) -> dict:
    """
    Main entry point. Attempts AI-assisted assessment first (if enabled and
    available), then always computes the deterministic fallback so we have
    a guaranteed, explainable score. If AI output looks valid, it's used
    for score/level/reasoning; the fallback reasons are still preserved as
    a transparent cross-check.
    """
    fallback = fallback_assessment(issue_type, heritage_type, description, severity, is_repeated)

    if not use_ai or not is_ollama_available():
        fallback["ai_used"] = False
        return fallback

    ai_result = analyze_report(description, issue_type, heritage_type, severity)

    if not ai_result or "risk_score" not in ai_result:
        fallback["ai_used"] = False
        return fallback

    try:
        ai_score = _clamp(int(ai_result.get("risk_score", fallback["score"])))
    except Exception:
        ai_score = fallback["score"]

    ai_level = ai_result.get("risk_level") or risk_level_from_score(ai_score)
    ai_reasons = ai_result.get("key_indicators") or fallback["reasons"]

    return {
        "score": ai_score,
        "level": ai_level,
        "reasons": ai_reasons,
        "source": "ollama-phi3",
        "category": ai_result.get("category", issue_type),
        "recommended_priority": ai_result.get("recommended_priority", _priority_for_level(ai_level)),
        "reasoning": ai_result.get("reasoning", ""),
        "ai_used": True,
        "fallback_score": fallback["score"],
        "fallback_level": fallback["level"],
    }
