"""
Analytics service: aggregate queries powering the dashboard and analytics page.
"""

from utils.database import fetch_all, fetch_one


def summary_counts() -> dict:
    total = fetch_one("SELECT COUNT(*) as c FROM reports")["c"]

    high_risk = fetch_one(
        """SELECT COUNT(DISTINCT r.report_id) as c FROM reports r
        JOIN risk_assessments ra ON r.report_id = ra.report_id
        WHERE ra.level IN ('HIGH','CRITICAL')
        AND ra.id = (SELECT MAX(id) FROM risk_assessments WHERE report_id = r.report_id)"""
    )["c"]

    pending_verification = fetch_one(
        "SELECT COUNT(*) as c FROM reports WHERE status IN ('AI_SCREENED','MORE_EVIDENCE_REQUESTED')"
    )["c"]

    verified = fetch_one(
        """SELECT COUNT(*) as c FROM reports WHERE status NOT IN
        ('SUBMITTED','AI_SCREENED','REJECTED','MORE_EVIDENCE_REQUESTED')"""
    )["c"]

    under_action = fetch_one(
        "SELECT COUNT(*) as c FROM reports WHERE status IN ('ASSIGNED','INSPECTION_SCHEDULED','ACTION_IN_PROGRESS')"
    )["c"]

    monitoring = fetch_one("SELECT COUNT(*) as c FROM reports WHERE status = 'MONITORING'")["c"]

    return {
        "total_reports": total,
        "high_risk": high_risk,
        "pending_verification": pending_verification,
        "verified": verified,
        "under_action": under_action,
        "monitoring": monitoring,
    }


def reports_by_state() -> list:
    return fetch_all("SELECT state, COUNT(*) as count FROM reports GROUP BY state ORDER BY count DESC")


def reports_by_heritage_type() -> list:
    return fetch_all(
        "SELECT heritage_type, COUNT(*) as count FROM reports GROUP BY heritage_type ORDER BY count DESC"
    )


def risk_distribution() -> list:
    return fetch_all(
        """SELECT ra.level as level, COUNT(*) as count FROM risk_assessments ra
        WHERE ra.id IN (SELECT MAX(id) FROM risk_assessments GROUP BY report_id)
        GROUP BY ra.level"""
    )


def issue_distribution() -> list:
    return fetch_all("SELECT issue_type, COUNT(*) as count FROM reports GROUP BY issue_type ORDER BY count DESC")


def verification_rate() -> dict:
    total = fetch_one("SELECT COUNT(DISTINCT report_id) as c FROM verifications")["c"]
    verified = fetch_one("SELECT COUNT(*) as c FROM verifications WHERE status = 'VERIFIED'")["c"]
    rejected = fetch_one("SELECT COUNT(*) as c FROM verifications WHERE status = 'REJECTED'")["c"]
    rate = round((verified / total) * 100, 1) if total else 0.0
    return {"total_reviewed": total, "verified": verified, "rejected": rejected, "verification_rate_pct": rate}


def recent_high_risk_cases(limit: int = 5) -> list:
    return fetch_all(
        """SELECT r.report_id, r.heritage_name, r.state, ra.level, ra.score
        FROM reports r JOIN risk_assessments ra ON r.report_id = ra.report_id
        WHERE ra.id = (SELECT MAX(id) FROM risk_assessments WHERE report_id = r.report_id)
        AND ra.level IN ('HIGH','CRITICAL')
        ORDER BY ra.score DESC LIMIT ?""",
        (limit,),
    )


def cases_over_time() -> list:
    return fetch_all(
        """SELECT substr(created_at,1,10) as day, COUNT(*) as count
        FROM reports GROUP BY day ORDER BY day ASC"""
    )
