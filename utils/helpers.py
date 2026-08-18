"""
General helper utilities: ID generation, JSON loading, formatting.
"""

import json
import os
import random
import string
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_json(filename: str):
    """Load a JSON file from the data/ directory. Returns {} on failure."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def generate_report_id() -> str:
    """Generate a unique heritage report ID like HEN-2026-00127."""
    year = datetime.now().year
    suffix = "".join(random.choices(string.digits, k=5))
    return f"HEN-{year}-{suffix}"


def risk_level_from_score(score: int) -> str:
    """Map a numeric risk score (0-100) to a risk level label."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def risk_color(level: str) -> str:
    colors = {
        "LOW": "#22C55E",
        "MEDIUM": "#F59E0B",
        "HIGH": "#FB923C",
        "CRITICAL": "#EF4444",
    }
    return colors.get(level, "#94A3B8")


def risk_emoji(level: str) -> str:
    emojis = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
    }
    return emojis.get(level, "⚪")


def status_badge(status: str) -> str:
    """Return a friendly label with icon for a case status."""
    icons = {
        "SUBMITTED": "📝 Submitted",
        "AI_SCREENED": "🧠 AI Screened",
        "PENDING_VERIFICATION": "🔎 Pending Verification",
        "VERIFIED": "✅ Verified",
        "REJECTED": "❌ Rejected",
        "MORE_EVIDENCE_REQUESTED": "📎 More Evidence Requested",
        "ALERTED": "🚨 Alerted",
        "ASSIGNED": "🏛 Assigned",
        "INSPECTION_SCHEDULED": "📅 Inspection Scheduled",
        "ACTION_IN_PROGRESS": "🚧 Action In Progress",
        "RESOLVED": "🟢 Resolved",
        "MONITORING": "📈 Monitoring",
    }
    return icons.get(status, status)


def safe_get(d: dict, key, default=""):
    try:
        return d.get(key, default) or default
    except Exception:
        return default


def truncate(text: str, length: int = 120) -> str:
    if not text:
        return ""
    return text if len(text) <= length else text[: length - 3] + "..."
