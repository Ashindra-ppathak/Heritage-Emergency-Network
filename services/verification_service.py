"""
Verification service: allows heritage experts to verify, reject, or request
more evidence for a report. AI never makes this final call — a human does.
"""

from utils.database import execute, fetch_all, fetch_one, now_iso
from services.report_service import update_status


def pending_verification_reports() -> list:
    """Reports that have been AI-screened but not yet verified/rejected."""
    return fetch_all(
        "SELECT * FROM reports WHERE status IN ('AI_SCREENED', 'MORE_EVIDENCE_REQUESTED') "
        "ORDER BY created_at DESC"
    )


def submit_verification(report_id: str, verifier_id: str, decision: str, notes: str = "") -> None:
    """
    decision must be one of: VERIFIED, REJECTED, MORE_EVIDENCE_REQUESTED
    """
    execute(
        """INSERT INTO verifications (report_id, verifier_id, status, notes, verified_at)
        VALUES (?, ?, ?, ?, ?)""",
        (report_id, verifier_id, decision, notes, now_iso()),
    )
    update_status(report_id, decision)


def get_verification_history(report_id: str) -> list:
    return fetch_all(
        "SELECT * FROM verifications WHERE report_id = ? ORDER BY id DESC", (report_id,)
    )


def latest_verification(report_id: str) -> dict:
    rows = get_verification_history(report_id)
    return rows[0] if rows else {}
