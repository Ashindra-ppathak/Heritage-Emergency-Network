"""
Monitoring & authority-action service: manages the ACT and MONITOR stages
of the workflow — assignment, inspection, resolution, and ongoing risk
trend tracking for verified/alerted cases.
"""

from utils.database import execute, fetch_all, fetch_one, now_iso
from services.report_service import update_status, get_latest_assessment
from ai.recommendation_engine import route_organization

ACTION_STATUS_FLOW = [
    "VERIFIED",
    "ASSIGNED",
    "INSPECTION_SCHEDULED",
    "ACTION_IN_PROGRESS",
    "RESOLVED",
    "MONITORING",
]


def cases_for_authority() -> list:
    """Verified or further-along cases visible to the Authority role."""
    return fetch_all(
        """SELECT * FROM reports WHERE status IN
        ('VERIFIED','ALERTED','ASSIGNED','INSPECTION_SCHEDULED','ACTION_IN_PROGRESS','RESOLVED')
        ORDER BY created_at DESC"""
    )


def record_action(report_id: str, action_type: str, assigned_to: str, status: str, notes: str = "") -> None:
    execute(
        """INSERT INTO actions (report_id, action_type, assigned_to, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (report_id, action_type, assigned_to, status, notes, now_iso()),
    )
    update_status(report_id, status)


def assign_case(report_id: str, notes: str = "") -> dict:
    report = fetch_one("SELECT * FROM reports WHERE report_id = ?", (report_id,))
    org = route_organization(report["issue_type"]) if report else {"name": "State Culture Department"}
    record_action(report_id, "Assign Team", org["name"], "ASSIGNED", notes or f"Assigned to {org['name']}")
    return org


def schedule_inspection(report_id: str, notes: str = "") -> None:
    record_action(report_id, "Schedule Inspection", "", "INSPECTION_SCHEDULED", notes)


def mark_in_progress(report_id: str, notes: str = "") -> None:
    record_action(report_id, "Mark Under Action", "", "ACTION_IN_PROGRESS", notes)


def request_expert(report_id: str, notes: str = "") -> None:
    record_action(report_id, "Request Expert", "Independent Conservation Expert", "ACTION_IN_PROGRESS", notes)


def mark_resolved(report_id: str, notes: str = "") -> None:
    record_action(report_id, "Mark Resolved", "", "RESOLVED", notes)


def get_action_history(report_id: str) -> list:
    return fetch_all("SELECT * FROM actions WHERE report_id = ? ORDER BY id ASC", (report_id,))


def move_to_monitoring(report_id: str, condition: str = "Stable", notes: str = "", next_review: str = "") -> None:
    assessment = get_latest_assessment(report_id)
    score = assessment.get("score", 0)
    execute(
        """INSERT INTO monitoring (report_id, risk_score, condition, notes, next_review, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (report_id, score, condition, notes, next_review, now_iso()),
    )
    update_status(report_id, "MONITORING")


def add_monitoring_update(report_id: str, risk_score: int, condition: str, notes: str = "", next_review: str = "") -> None:
    execute(
        """INSERT INTO monitoring (report_id, risk_score, condition, notes, next_review, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (report_id, risk_score, condition, notes, next_review, now_iso()),
    )


def get_monitoring_history(report_id: str) -> list:
    return fetch_all("SELECT * FROM monitoring WHERE report_id = ? ORDER BY id ASC", (report_id,))


def cases_under_monitoring() -> list:
    return fetch_all("SELECT * FROM reports WHERE status = 'MONITORING' ORDER BY created_at DESC")
