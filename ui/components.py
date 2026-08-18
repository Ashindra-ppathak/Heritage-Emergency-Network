"""
Reusable UI components for Heritage Emergency Network (Streamlit).
"""

import streamlit as st
from utils.helpers import risk_emoji

WORKFLOW_STAGES = ["REPORT", "AI SCREEN", "VERIFY", "ALERT", "ACT", "MONITOR"]

STATUS_TO_STAGE_INDEX = {
    "SUBMITTED": 0,
    "AI_SCREENED": 1,
    "PENDING_VERIFICATION": 1,
    "MORE_EVIDENCE_REQUESTED": 1,
    "VERIFIED": 2,
    "REJECTED": 2,
    "ALERTED": 3,
    "ASSIGNED": 4,
    "INSPECTION_SCHEDULED": 4,
    "ACTION_IN_PROGRESS": 4,
    "RESOLVED": 4,
    "MONITORING": 5,
}


def badge_class(level: str) -> str:
    return f"badge-{level.lower()}" if level else "badge-low"


def risk_badge_html(level: str, score: int = None) -> str:
    score_txt = f" {score}/100" if score is not None else ""
    return f'<span class="hen-badge {badge_class(level)}">{risk_emoji(level)} {level}{score_txt}</span>'


def hero_header(title: str, tagline: str, subtext: str = ""):
    st.markdown(
        f"""
        <div class="hen-hero">
            <div class="hen-title">{title}</div>
            <div class="hen-tagline">{tagline}</div>
            <div class="hen-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value):
    st.markdown(
        f"""
        <div class="hen-card">
            <div class="hen-metric-value">{value}</div>
            <div class="hen-metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ai_disclaimer():
    st.markdown(
        """
        <div class="hen-disclaimer">
        ⚠️ <b>AI Preliminary Assessment</b> — For screening and prioritization only.
        Final verification requires qualified human review. This is not an official
        heritage condition assessment.
        </div>
        """,
        unsafe_allow_html=True,
    )


def prototype_disclaimer(text: str = None):
    st.markdown(
        f"""
        <div class="hen-disclaimer">
        ℹ️ {text or "This is a prototype simulation. Organizations and workflows shown are demo entities — no real government integration exists."}
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_tracker(status: str):
    """Render the REPORT -> AI SCREEN -> VERIFY -> ALERT -> ACT -> MONITOR tracker."""
    current_index = STATUS_TO_STAGE_INDEX.get(status, 0)
    rejected = status == "REJECTED"

    html = '<div style="margin: 12px 0;">'
    for i, stage in enumerate(WORKFLOW_STAGES):
        if rejected and i >= 2:
            css_class = ""
            icon = "○"
        elif i < current_index:
            css_class = "done"
            icon = "✓"
        elif i == current_index:
            css_class = "active"
            icon = "●" if not rejected else "✕"
        else:
            css_class = ""
            icon = "○"
        html += f'<span class="hen-workflow-step {css_class}">{icon} {stage}</span>'
        if i < len(WORKFLOW_STAGES) - 1:
            html += ' <span style="color:#24324A;">→</span> '
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def case_summary_card(report: dict, risk_level: str = None, risk_score=None):
    level = risk_level or "LOW"
    st.markdown(
        f"""
        <div class="hen-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:16px; font-weight:700;">{report.get('heritage_name','')}</div>
                    <div style="font-size:12.5px; color:#94A3B8;">{report.get('state','')} • {report.get('issue_type','')} • {report.get('report_id','')}</div>
                </div>
                <div>{risk_badge_html(level, risk_score)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str, icon: str = ""):
    st.markdown(f"### {icon} {text}" if icon else f"### {text}")
