"""
Report service: handles creation and retrieval of heritage risk reports,
plus triggering the AI preliminary risk assessment.
"""

from utils.database import execute, fetch_all, fetch_one, now_iso
from utils.helpers import generate_report_id
from ai.risk_assessor import assess_risk
from ai.report_analyzer import analyze
import json


def _count_similar_reports(heritage_name: str, state: str) -> int:
    rows = fetch_all(
        "SELECT COUNT(*) as c FROM reports WHERE heritage_name = ? AND state = ?",
        (heritage_name, state),
    )
    return rows[0]["c"] if rows else 0


def create_report(
    heritage_name: str,
    heritage_type: str,
    state: str,
    district: str,
    location: str,
    description: str,
    issue_type: str,
    reported_severity: str,
    date_observed: str,
    image_path: str = "",
    reporter_id=None,
    use_ai: bool = True,
) -> dict:
    """
    Create a new heritage report, run AI preliminary risk assessment,
    and persist both the report and its risk assessment. Returns a dict
    with report_id and the assessment result.
    """
    report_id = generate_report_id()
    created_at = now_iso()

    is_repeated = _count_similar_reports(heritage_name, state) > 0

    execute(
        """INSERT INTO reports
        (report_id, heritage_name, heritage_type, state, district, location,
         description, issue_type, reported_severity, date_observed, image_path,
         reporter_id, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            report_id, heritage_name, heritage_type, state, district, location,
            description, issue_type, reported_severity, date_observed, image_path,
            reporter_id, created_at, "SUBMITTED",
        ),
    )

    assessment = assess_risk(
        issue_type=issue_type,
        heritage_type=heritage_type,
        description=description,
        severity=reported_severity,
        is_repeated=is_repeated,
        use_ai=use_ai,
    )
    analysis = analyze(description, issue_type, heritage_type, use_ai=use_ai)

    execute(
        """INSERT INTO risk_assessments
        (report_id, score, level, reasons, ai_analysis, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            report_id,
            assessment["score"],
            assessment["level"],
            json.dumps(assessment.get("reasons", [])),
            json.dumps({**assessment, **analysis}, default=str),
            assessment.get("source", "fallback"),
            now_iso(),
        ),
    )

    execute(
        "UPDATE reports SET status = ? WHERE report_id = ?",
        ("AI_SCREENED", report_id),
    )

    return {"report_id": report_id, "assessment": assessment, "analysis": analysis, "is_repeated": is_repeated}


def get_report(report_id: str) -> dict:
    return fetch_one("SELECT * FROM reports WHERE report_id = ?", (report_id,))


def get_latest_assessment(report_id: str) -> dict:
    rows = fetch_all(
        "SELECT * FROM risk_assessments WHERE report_id = ? ORDER BY id DESC LIMIT 1",
        (report_id,),
    )
    if not rows:
        return {}
    row = rows[0]
    try:
        row["reasons_parsed"] = json.loads(row.get("reasons") or "[]")
    except Exception:
        row["reasons_parsed"] = []
    try:
        row["ai_analysis_parsed"] = json.loads(row.get("ai_analysis") or "{}")
    except Exception:
        row["ai_analysis_parsed"] = {}
    return row


def list_reports(status: str = None, state: str = None, heritage_type: str = None, limit: int = 500) -> list:
    query = "SELECT * FROM reports WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if state:
        query += " AND state = ?"
        params.append(state)
    if heritage_type:
        query += " AND heritage_type = ?"
        params.append(heritage_type)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return fetch_all(query, tuple(params))


def list_reports_with_risk(limit: int = 500) -> list:
    """Join reports with their latest risk assessment for dashboard/map views."""
    query = """
    SELECT r.*, ra.score as risk_score, ra.level as risk_level
    FROM reports r
    LEFT JOIN (
        SELECT report_id, score, level, MAX(id) as max_id
        FROM risk_assessments GROUP BY report_id
    ) ra ON r.report_id = ra.report_id
    ORDER BY r.created_at DESC LIMIT ?
    """
    return fetch_all(query, (limit,))


def update_status(report_id: str, status: str):
    execute("UPDATE reports SET status = ? WHERE report_id = ?", (status, report_id))
