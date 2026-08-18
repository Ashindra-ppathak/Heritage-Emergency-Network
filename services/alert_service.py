"""
Alert service: creates high-priority alerts for verified, high-risk cases
and routes them to a prototype target organization.
"""

from utils.database import execute, fetch_all, fetch_one, now_iso
from services.report_service import get_report, get_latest_assessment, update_status
from ai.recommendation_engine import route_organization, recommend_action

ALERT_RISK_THRESHOLD = 75


def maybe_create_alert(report_id: str) -> dict:
    """
    Create an alert if: risk score >= threshold AND report is VERIFIED.
    Returns the alert dict if created, else {}.
    """
    report = get_report(report_id)
    if not report or report.get("status") != "VERIFIED":
        return {}

    assessment = get_latest_assessment(report_id)
    score = assessment.get("score", 0)
    if score < ALERT_RISK_THRESHOLD:
        return {}

    org = route_organization(report["issue_type"])
    action = recommend_action(report["issue_type"])
    message = (
        f"HIGH PRIORITY HERITAGE ALERT — {report['heritage_name']} ({report['state']}). "
        f"Risk {score}/100. Recommended action: {action}."
    )

    execute(
        """INSERT INTO alerts (report_id, target_organization, priority, message, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        (report_id, org["name"], assessment.get("level", "HIGH"), message, now_iso()),
    )
    update_status(report_id, "ALERTED")

    return {
        "report_id": report_id,
        "target_organization": org["name"],
        "priority": assessment.get("level", "HIGH"),
        "message": message,
        "recommended_action": action,
    }


def list_alerts(limit: int = 200) -> list:
    return fetch_all("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))


def get_alert_for_report(report_id: str) -> dict:
    rows = fetch_all(
        "SELECT * FROM alerts WHERE report_id = ? ORDER BY id DESC LIMIT 1", (report_id,)
    )
    return rows[0] if rows else {}
