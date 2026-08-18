"""
Page rendering functions for Heritage Emergency Network.
Each function renders one page of the Streamlit app.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import json
import random

from utils.helpers import load_json, risk_emoji, status_badge, truncate
from utils.image_utils import save_uploaded_image, image_exists, basic_damage_indicators
from ai.ollama_client import is_ollama_available
from ai.recommendation_engine import route_organization, organizations_disclaimer

from services import report_service, verification_service, alert_service, monitoring_service, analytics_service

from ui.components import (
    hero_header, metric_card, ai_disclaimer, prototype_disclaimer,
    workflow_tracker, case_summary_card, section_title, risk_badge_html,
)

ISSUE_DATA = load_json("issue_types.json")
HERITAGE_DATA = load_json("heritage_sites.json")

PLOTLY_DARK = {
    "paper_bgcolor": "#0F1626",
    "plot_bgcolor": "#0F1626",
    "font_color": "#F8FAFC",
}


def _style_fig(fig):
    fig.update_layout(
        paper_bgcolor=PLOTLY_DARK["paper_bgcolor"],
        plot_bgcolor=PLOTLY_DARK["plot_bgcolor"],
        font_color=PLOTLY_DARK["font_color"],
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

def render_dashboard():
    hero_header(
        "HERITAGE EMERGENCY NETWORK",
        '"Protect Heritage Before It Is Lost."',
        "AI-assisted early warning and coordinated action for India's cultural heritage.",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 Report Heritage at Risk", use_container_width=True):
            st.session_state.page = "📍 Report Heritage"
            st.rerun()
    with c2:
        if st.button("🗺 View Risk Map", use_container_width=True):
            st.session_state.page = "🗺 Heritage Risk Map"
            st.rerun()

    st.write("")
    counts = analytics_service.summary_counts()
    cols = st.columns(6)
    labels = [
        ("Total Reports", counts["total_reports"]),
        ("High Risk", counts["high_risk"]),
        ("Pending Verification", counts["pending_verification"]),
        ("Verified", counts["verified"]),
        ("Under Action", counts["under_action"]),
        ("Monitoring", counts["monitoring"]),
    ]
    for col, (label, value) in zip(cols, labels):
        with col:
            metric_card(label, value)

    st.write("")
    section_title("Recent High-Risk Cases", "🚨")
    high_risk_cases = analytics_service.recent_high_risk_cases(limit=6)
    if not high_risk_cases:
        st.info("No high-risk cases yet. Submit a report or run Demo Mode from the sidebar.")
    else:
        for case in high_risk_cases:
            case_summary_card(
                {"heritage_name": case["heritage_name"], "state": case["state"],
                 "issue_type": "", "report_id": case["report_id"]},
                risk_level=case["level"], risk_score=case["score"],
            )

    ollama_status = "🟢 Connected (Phi-3 active)" if is_ollama_available() else "🟡 Offline — using deterministic fallback engine"
    st.caption(f"AI Engine Status: {ollama_status}")


# ---------------------------------------------------------------------------
# REPORT HERITAGE
# ---------------------------------------------------------------------------

def render_report_page():
    hero_header(
        "REPORT HERITAGE AT RISK",
        "Your report can help protect a piece of India's cultural memory.",
        "",
    )

    heritage_types = ISSUE_DATA.get("heritage_types", [])
    issue_types = ISSUE_DATA.get("issue_types", [])
    severities = ISSUE_DATA.get("severity_levels", ["Low", "Medium", "High", "Critical"])
    states = HERITAGE_DATA.get("states", [])

    with st.form("report_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            heritage_name = st.text_input("Heritage Name *", placeholder="e.g. Historic Stepwell")
            heritage_type = st.selectbox("Heritage Type *", heritage_types)
            state = st.selectbox("State *", states)
            district = st.text_input("District", placeholder="e.g. Patan")
        with col2:
            location = st.text_input("Location / Landmark", placeholder="e.g. Near old market road")
            issue_type = st.selectbox("Issue Type *", issue_types)
            date_observed = st.date_input("Date Observed", value=date.today())
            severity = st.selectbox("Severity Noticed by Reporter", severities, index=1)

        description = st.text_area(
            "Description *",
            placeholder="Describe what you observed — visible damage, cause, extent, urgency...",
            height=120,
        )
        image = st.file_uploader("Upload Photo (optional)", type=["jpg", "jpeg", "png"])

        use_ai = st.checkbox("Use AI-assisted analysis (Ollama / Phi-3) if available", value=True)

        submitted = st.form_submit_button("Submit Report", use_container_width=True)

    if submitted:
        if not heritage_name or not description:
            st.error("Please fill in at least Heritage Name and Description.")
            return

        with st.spinner("Submitting report and running AI preliminary screening..."):
            result = report_service.create_report(
                heritage_name=heritage_name,
                heritage_type=heritage_type,
                state=state,
                district=district,
                location=location,
                description=description,
                issue_type=issue_type,
                reported_severity=severity,
                date_observed=str(date_observed),
                image_path=save_uploaded_image(image, "TEMP") if image else "",
                use_ai=use_ai,
            )

        st.success(f"✅ Report successfully submitted. Report ID: **{result['report_id']}**")
        st.session_state.last_report_id = result["report_id"]
        _render_assessment_result(result["assessment"], result["analysis"])

        if st.button("View Full Case File →"):
            st.session_state.view_report_id = result["report_id"]
            st.session_state.page = "🧠 AI Risk Assessment"
            st.rerun()


def _render_assessment_result(assessment: dict, analysis: dict = None):
    section_title("AI Preliminary Assessment", "🧠")
    ai_disclaimer()

    level = assessment.get("level", "LOW")
    score = assessment.get("score", 0)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(risk_badge_html(level, score), unsafe_allow_html=True)
        st.metric("Risk Score", f"{score} / 100")
    with c2:
        st.write("**Reasons:**")
        reasons = assessment.get("reasons", [])
        if isinstance(reasons, str):
            try:
                reasons = json.loads(reasons)
            except Exception:
                reasons = [reasons]
        for r in reasons:
            st.write(f"- {r}")

    if assessment.get("reasoning"):
        st.write(f"**AI Reasoning:** {assessment['reasoning']}")

    st.caption(f"Recommended priority: {assessment.get('recommended_priority', 'Review recommended')}")
    st.caption(f"Analysis source: {'Ollama (Phi-3)' if assessment.get('ai_used') else 'Deterministic fallback engine'}")

    if analysis:
        with st.expander("Evidence Summary & Detected Keywords"):
            st.write(analysis.get("evidence_summary", ""))
            if analysis.get("detected_keywords"):
                st.write("Detected keywords: " + ", ".join(analysis["detected_keywords"]))
            st.write(f"Urgency signal: {analysis.get('urgency', 'Normal')}")
            if analysis.get("ai_reasoning"):
                st.write(f"AI note: {analysis['ai_reasoning']}")

# ---------------------------------------------------------------------------
# AI RISK ASSESSMENT / CASE FILE
# ---------------------------------------------------------------------------

def render_case_file_page():
    hero_header("HERITAGE CASE FILE", "AI-assisted preliminary risk assessment & full case history", "")

    all_reports = report_service.list_reports_with_risk(limit=500)
    if not all_reports:
        st.info("No reports yet. Submit a report from '📍 Report Heritage' or try Demo Mode in the sidebar.")
        return

    default_id = st.session_state.get("view_report_id") or st.session_state.get("last_report_id")
    id_list = [r["report_id"] for r in all_reports]
    default_index = id_list.index(default_id) if default_id in id_list else 0

    report_id = st.selectbox(
        "Select a Report ID",
        id_list,
        index=default_index,
        format_func=lambda rid: f"{rid} — {next((r['heritage_name'] for r in all_reports if r['report_id']==rid), '')}",
    )
    st.session_state.view_report_id = report_id
    _render_case_detail(report_id)


def _render_case_detail(report_id: str):
    report = report_service.get_report(report_id)
    if not report:
        st.error("Report not found.")
        return

    assessment = report_service.get_latest_assessment(report_id)

    st.markdown(f"### HERITAGE CASE — `{report_id}`")
    workflow_tracker(report.get("status", "SUBMITTED"))

    col1, col2 = st.columns([1, 2])
    with col1:
        if image_exists(report.get("image_path", "")):
            st.image(report["image_path"], use_container_width=True, caption="Reported photo")
        else:
            st.caption("No photo was attached to this report.")
    with col2:
        st.write(f"**Heritage Name:** {report.get('heritage_name')}")
        st.write(f"**Heritage Type:** {report.get('heritage_type')}")
        st.write(f"**Location:** {report.get('location') or '—'}, {report.get('district') or '—'}, {report.get('state')}")
        st.write(f"**Issue Type:** {report.get('issue_type')}")
        st.write(f"**Date Observed:** {report.get('date_observed')}")
        st.write(f"**Reported Severity:** {report.get('reported_severity')}")
        st.write(f"**Status:** {status_badge(report.get('status',''))}")
        st.write(f"**Description:** {report.get('description')}")

    st.divider()
    section_title("AI Preliminary Assessment", "🧠")
    ai_disclaimer()

    if assessment:
        level = assessment.get("level", "LOW")
        score = assessment.get("score", 0)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(risk_badge_html(level, score), unsafe_allow_html=True)
            st.metric("Risk Score", f"{score} / 100")
            st.caption(f"Source: {'Ollama (Phi-3)' if assessment.get('source')=='ollama-phi3' else 'Deterministic fallback engine'}")
        with c2:
            st.write("**Reasons:**")
            for r in assessment.get("reasons_parsed", []):
                st.write(f"- {r}")
            ai_analysis = assessment.get("ai_analysis_parsed", {})
            if ai_analysis.get("recommended_next_action"):
                st.caption(f"Recommended next action: {ai_analysis['recommended_next_action']}")

        indicators = basic_damage_indicators(report.get("image_path", ""))
        if indicators:
            with st.expander("Illustrative Visual Indicators (heuristic, not real damage detection)"):
                for i in indicators:
                    st.write(f"- {i}")
    else:
        st.info("No AI assessment recorded for this report yet.")

    st.divider()
    section_title("Verification History", "🔎")
    v_history = verification_service.get_verification_history(report_id)
    if v_history:
        for v in v_history:
            st.write(f"**{v['status']}** by {v.get('verifier_id') or 'verifier'} on {v['verified_at']}")
            if v.get("notes"):
                st.caption(v["notes"])
    else:
        st.caption("Not yet reviewed by a verifier.")

    alert = alert_service.get_alert_for_report(report_id)
    if alert:
        st.divider()
        section_title("Alert", "🚨")
        st.error(alert["message"])
        st.caption(f"Routed to: {alert['target_organization']} • Priority: {alert['priority']}")

    st.divider()
    section_title("Action History", "🏛")
    actions = monitoring_service.get_action_history(report_id)
    if actions:
        for a in actions:
            st.write(f"**{a['action_type']}** → {a['status']} ({a['created_at']})")
            if a.get("assigned_to"):
                st.caption(f"Assigned to: {a['assigned_to']}")
    else:
        st.caption("No authority actions recorded yet.")

    mon_history = monitoring_service.get_monitoring_history(report_id)
    if mon_history:
        st.divider()
        section_title("Monitoring Trend", "📈")
        df = pd.DataFrame(mon_history)
        fig = px.line(df, x="created_at", y="risk_score", markers=True, title="Risk score over time")
        st.plotly_chart(_style_fig(fig), use_container_width=True)


# ---------------------------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------------------------

def render_verification_page():
    hero_header("VERIFICATION", "Human experts review AI-screened reports before any action is taken.", "")
    prototype_disclaimer("AI never makes the final call. A qualified verifier must confirm, reject, or request more evidence.")

    pending = verification_service.pending_verification_reports()
    if not pending:
        st.success("No reports currently pending verification.")
        return

    for report in pending:
        assessment = report_service.get_latest_assessment(report["report_id"])
        with st.expander(f"{report['heritage_name']} — {report['state']} — {report['report_id']}", expanded=False):
            col1, col2 = st.columns([1, 2])
            with col1:
                if image_exists(report.get("image_path", "")):
                    st.image(report["image_path"], use_container_width=True)
                if assessment:
                    st.markdown(risk_badge_html(assessment.get("level", "LOW"), assessment.get("score", 0)), unsafe_allow_html=True)
            with col2:
                st.write(f"**Issue:** {report['issue_type']}  |  **Type:** {report['heritage_type']}")
                st.write(f"**Description:** {report['description']}")
                if assessment:
                    st.write("**AI Reasons:**")
                    for r in assessment.get("reasons_parsed", []):
                        st.write(f"- {r}")

            notes = st.text_area("Verifier notes", key=f"notes_{report['report_id']}", height=70)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✅ Verify", key=f"verify_{report['report_id']}", use_container_width=True):
                    verification_service.submit_verification(report["report_id"], "Dr. Verifier (Demo)", "VERIFIED", notes)
                    alert_service.maybe_create_alert(report["report_id"])
                    st.success("Case verified.")
                    st.rerun()
            with c2:
                if st.button("📎 Request More Evidence", key=f"more_{report['report_id']}", use_container_width=True):
                    verification_service.submit_verification(report["report_id"], "Dr. Verifier (Demo)", "MORE_EVIDENCE_REQUESTED", notes)
                    st.info("More evidence requested.")
                    st.rerun()
            with c3:
                if st.button("❌ Reject", key=f"reject_{report['report_id']}", use_container_width=True):
                    verification_service.submit_verification(report["report_id"], "Dr. Verifier (Demo)", "REJECTED", notes)
                    st.warning("Case rejected.")
                    st.rerun()


# ---------------------------------------------------------------------------
# ALERTS
# ---------------------------------------------------------------------------

def render_alerts_page():
    hero_header("HERITAGE ALERTS", "High-priority, verified cases routed to prototype response organizations.", "")
    prototype_disclaimer(organizations_disclaimer())

    alerts = alert_service.list_alerts()
    if not alerts:
        st.info("No alerts have been generated yet. Alerts are created automatically when a VERIFIED case has risk ≥ 75.")
        return

    for a in alerts:
        report = report_service.get_report(a["report_id"])
        st.markdown(
            f"""
            <div class="hen-card">
                <div style="font-weight:800; color:#EF4444;">🚨 HIGH PRIORITY HERITAGE ALERT</div>
                <div style="font-size:16px; font-weight:700; margin-top:6px;">{report['heritage_name'] if report else ''}</div>
                <div style="color:#94A3B8; font-size:13px;">Location: {report['state'] if report else ''} • Report: {a['report_id']}</div>
                <div style="margin-top:8px;">{a['message']}</div>
                <div style="margin-top:8px; font-size:13px;">Target organization (prototype): <b>{a['target_organization']}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# AUTHORITY ACTION
# ---------------------------------------------------------------------------

def render_authority_page():
    hero_header("AUTHORITY ACTION", "Simulated authority workflow — assign, inspect, act, and resolve verified cases.", "")
    prototype_disclaimer("This simulates an authority workflow. No real government office is connected.")

    cases = monitoring_service.cases_for_authority()
    if not cases:
        st.info("No verified cases available for authority action yet.")
        return

    for report in cases:
        assessment = report_service.get_latest_assessment(report["report_id"])
        with st.expander(f"{report['heritage_name']} — {status_badge(report['status'])} — {report['report_id']}"):
            workflow_tracker(report["status"])
            if assessment:
                st.markdown(risk_badge_html(assessment.get("level", "LOW"), assessment.get("score", 0)), unsafe_allow_html=True)
            st.write(f"**Issue:** {report['issue_type']}  |  **Location:** {report['state']}")

            notes = st.text_area("Notes", key=f"anotes_{report['report_id']}", height=60)
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("Assign Team", key=f"assign_{report['report_id']}"):
                    org = monitoring_service.assign_case(report["report_id"], notes)
                    st.success(f"Assigned to {org['name']}")
                    st.rerun()
            with c2:
                if st.button("Schedule Inspection", key=f"insp_{report['report_id']}"):
                    monitoring_service.schedule_inspection(report["report_id"], notes)
                    st.success("Inspection scheduled.")
                    st.rerun()
            with c3:
                if st.button("Mark Under Action", key=f"prog_{report['report_id']}"):
                    monitoring_service.mark_in_progress(report["report_id"], notes)
                    st.success("Marked under action.")
                    st.rerun()
            with c4:
                if st.button("Request Expert", key=f"expert_{report['report_id']}"):
                    monitoring_service.request_expert(report["report_id"], notes)
                    st.success("Expert requested.")
                    st.rerun()
            with c5:
                if st.button("Mark Resolved", key=f"resolved_{report['report_id']}"):
                    monitoring_service.mark_resolved(report["report_id"], notes)
                    st.success("Marked resolved.")
                    st.rerun()

            if report["status"] == "RESOLVED":
                if st.button("📈 Move to Monitoring", key=f"mon_{report['report_id']}"):
                    monitoring_service.move_to_monitoring(report["report_id"], condition="Stable", notes="Initial monitoring entry")
                    st.success("Case moved to monitoring.")
                    st.rerun()


# ---------------------------------------------------------------------------
# MONITORING
# ---------------------------------------------------------------------------

def render_monitoring_page():
    hero_header("MONITORING", "Ongoing tracking of cases after intervention — the final stage of the workflow.", "")

    cases = monitoring_service.cases_under_monitoring()
    if not cases:
        st.info("No cases under monitoring yet. Resolve a case in Authority Action and move it to monitoring.")
        return

    for report in cases:
        history = monitoring_service.get_monitoring_history(report["report_id"])
        with st.expander(f"{report['heritage_name']} — {report['state']} — {report['report_id']}", expanded=False):
            workflow_tracker("MONITORING")
            if history:
                df = pd.DataFrame(history)
                fig = px.line(df, x="created_at", y="risk_score", markers=True, title="Simulated risk trend")
                st.plotly_chart(_style_fig(fig), use_container_width=True)
                latest = history[-1]
                st.write(f"**Current condition:** {latest['condition']}  |  **Current risk:** {latest['risk_score']}/100")
                st.write(f"**Last inspection:** {latest['created_at']}  |  **Next review:** {latest.get('next_review') or 'Not scheduled'}")

            st.write("**Add monitoring update (simulated)**")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_score = st.slider("Updated risk score", 0, 100, max(0, (history[-1]["risk_score"] - 15) if history else 50), key=f"score_{report['report_id']}")
            with c2:
                condition = st.selectbox("Condition", ["Improving", "Stable", "Deteriorating"], key=f"cond_{report['report_id']}")
            with c3:
                next_review = st.date_input("Next review date", key=f"next_{report['report_id']}")
            update_notes = st.text_input("Notes", key=f"upnotes_{report['report_id']}")
            if st.button("Add Monitoring Update", key=f"addmon_{report['report_id']}"):
                monitoring_service.add_monitoring_update(
                    report["report_id"], new_score, condition, update_notes, str(next_review)
                )
                st.success("Monitoring update recorded.")
                st.rerun()


# ---------------------------------------------------------------------------
# HERITAGE RISK MAP
# ---------------------------------------------------------------------------

STATE_COORDS = {
    "Andhra Pradesh": (15.9129, 79.7400), "Assam": (26.2006, 92.9376), "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661), "Goa": (15.2993, 74.1240), "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856), "Himachal Pradesh": (31.1048, 77.1734), "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139), "Kerala": (10.8505, 76.2711), "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139), "Odisha": (20.9517, 85.0985), "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179), "Tamil Nadu": (11.1271, 78.6569), "Telangana": (18.1124, 79.0193),
    "Uttar Pradesh": (26.8467, 80.9462), "Uttarakhand": (30.0668, 79.0193), "West Bengal": (22.9868, 87.8550),
}

RISK_MARKER_COLOR = {"LOW": "#22C55E", "MEDIUM": "#F59E0B", "HIGH": "#FB923C", "CRITICAL": "#EF4444"}


def render_map_page():
    hero_header("HERITAGE RISK MAP", "Simulated geographic view of reported heritage-risk cases across India.", "")

    reports = report_service.list_reports_with_risk(limit=500)
    if not reports:
        st.info("No reports yet to plot on the map.")
        return

    states = HERITAGE_DATA.get("states", [])
    types = ISSUE_DATA.get("heritage_types", [])
    c1, c2, c3 = st.columns(3)
    with c1:
        f_state = st.selectbox("Filter by State", ["All"] + states)
    with c2:
        f_type = st.selectbox("Filter by Heritage Type", ["All"] + types)
    with c3:
        f_risk = st.selectbox("Filter by Risk", ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

    rows = []
    for r in reports:
        if f_state != "All" and r["state"] != f_state:
            continue
        if f_type != "All" and r["heritage_type"] != f_type:
            continue
        level = r.get("risk_level") or "LOW"
        if f_risk != "All" and level != f_risk:
            continue
        lat, lon = STATE_COORDS.get(r["state"], (22.0, 79.0))
        jitter = (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6))
        rows.append({
            "lat": lat + jitter[0], "lon": lon + jitter[1],
            "name": r["heritage_name"], "state": r["state"], "risk": level,
            "score": r.get("risk_score") or 0, "status": r["status"], "report_id": r["report_id"],
            "issue": r["issue_type"],
        })

    if not rows:
        st.warning("No reports match the selected filters.")
        return

    df = pd.DataFrame(rows)
    fig = px.scatter_geo(
        df, lat="lat", lon="lon", color="risk",
        color_discrete_map=RISK_MARKER_COLOR,
        hover_name="name",
        hover_data={"state": True, "score": True, "status": True, "report_id": True, "issue": True, "lat": False, "lon": False},
        scope="asia", size="score" if df["score"].sum() > 0 else None,
    )
    fig.update_geos(
        center=dict(lat=22.5, lon=80), projection_scale=4.2,
        showcountries=True, countrycolor="#24324A",
        landcolor="#0F1626", bgcolor="#070B14", showland=True,
    )
    fig = _style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("🟢 Low   🟡 Medium   🟠 High   🔴 Critical — points are approximate/jittered for demo visualization.")

    section_title("Cases in view", "📍")
    st.dataframe(
        df[["report_id", "name", "state", "issue", "risk", "score", "status"]].rename(
            columns={"report_id": "Report ID", "name": "Heritage", "state": "State", "issue": "Issue", "risk": "Risk", "score": "Score", "status": "Status"}
        ),
        use_container_width=True, hide_index=True,
    )


# ---------------------------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------------------------

def render_analytics_page():
    hero_header("ANALYTICS", "Aggregate insight across all heritage-risk reports in the system.", "")

    counts = analytics_service.summary_counts()
    cols = st.columns(6)
    labels = [
        ("Total Reports", counts["total_reports"]), ("High Risk", counts["high_risk"]),
        ("Pending Verification", counts["pending_verification"]), ("Verified", counts["verified"]),
        ("Under Action", counts["under_action"]), ("Monitoring", counts["monitoring"]),
    ]
    for col, (label, value) in zip(cols, labels):
        with col:
            metric_card(label, value)

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        data = analytics_service.reports_by_state()
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(df, x="state", y="count", title="Reports by State", color_discrete_sequence=["#5B8CFF"])
            st.plotly_chart(_style_fig(fig), use_container_width=True)
    with c2:
        data = analytics_service.reports_by_heritage_type()
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(df, x="heritage_type", y="count", title="Reports by Heritage Type", color_discrete_sequence=["#8B5CF6"])
            st.plotly_chart(_style_fig(fig), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        data = analytics_service.risk_distribution()
        if data:
            df = pd.DataFrame(data)
            fig = px.pie(df, names="level", values="count", title="Risk Distribution",
                         color="level", color_discrete_map=RISK_MARKER_COLOR, hole=0.45)
            st.plotly_chart(_style_fig(fig), use_container_width=True)
    with c4:
        data = analytics_service.issue_distribution()
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(df, x="issue_type", y="count", title="Issue Type Distribution", color_discrete_sequence=["#F59E0B"])
            st.plotly_chart(_style_fig(fig), use_container_width=True)

    vr = analytics_service.verification_rate()
    section_title("Verification Rate", "🔎")
    st.write(f"**{vr['verification_rate_pct']}%** of reviewed cases were verified ({vr['verified']} verified / {vr['rejected']} rejected / {vr['total_reviewed']} total reviewed).")

    over_time = analytics_service.cases_over_time()
    if over_time:
        section_title("Reports Over Time", "📈")
        df = pd.DataFrame(over_time)
        fig = px.line(df, x="day", y="count", markers=True, title="Reports submitted per day", color_discrete_sequence=["#5B8CFF"])
        st.plotly_chart(_style_fig(fig), use_container_width=True)


# ---------------------------------------------------------------------------
# ABOUT
# ---------------------------------------------------------------------------

def render_about_page():
    hero_header("ABOUT", "Heritage Emergency Network — Project Overview", "")

    st.markdown("""
### The Problem
India's cultural heritage — monuments, temples, forts, stepwells, traditional crafts, folk
traditions, and festivals — faces ongoing risk from neglect, environmental damage, vandalism,
unauthorized construction, urban pressure, natural disasters, and the quiet disappearance of
traditional practices. Scattered citizen observations rarely reach the right people in time.

### The Solution
Heritage Emergency Network turns scattered citizen observations into structured, prioritized
heritage-risk cases through a clear workflow:

**REPORT → AI SCREEN → VERIFY → ALERT → ACT → MONITOR**

### Innovation
AI (via a locally running Phi-3 model through Ollama) is used only for **early screening and
prioritization** — never for final decisions. Human experts remain responsible for verification,
and human authorities remain responsible for action. If Ollama is not available, a transparent,
deterministic rule-based engine takes over so the platform keeps working.

### Why This Is Different
This is not a tourism site, a chatbot, or a generic complaint form. It is a coordination layer
that also treats **intangible heritage** — crafts, oral traditions, festivals — as seriously as
physical monuments, with its own risk factors like declining practitioners and loss of
documentation.

### Future Scope
- Official authority integrations
- Verified GIS / satellite imagery-based monitoring
- Multilingual reporting
- Real image-based damage detection
- Expert reviewer networks
- Community heritage archives
- Real-time disaster alerts
- Mobile application

### Limitations (Prototype)
- Organizations shown are **prototype/demo entities** — no real institutional integration exists.
- AI provides **preliminary screening only**, not scientific structural assessment or official
  certification.
- Map coordinates are approximate (state-level, jittered for visualization).
""")
    prototype_disclaimer()


# ---------------------------------------------------------------------------
# DEMO MODE
# ---------------------------------------------------------------------------

DEMO_SCENARIOS = {
    "Structural Damage (Historic Stepwell, Gujarat)": dict(
        heritage_name="Rani ki Vav Adjacent Stepwell", heritage_type="Stepwell", state="Gujarat",
        district="Patan", location="Near old market road", issue_type="Structural Damage",
        description="Visible cracks along the main stepwell wall, water seepage after monsoon, "
                     "and crumbling stonework near the entrance staircase. Damage appears to be worsening "
                     "and may become irreversible without urgent intervention.",
        reported_severity="Critical",
    ),
    "Tradition at Risk (Traditional Craft, Chhattisgarh)": dict(
        heritage_name="Bastar Terracotta Craft", heritage_type="Traditional Craft", state="Chhattisgarh",
        district="Bastar", location="Kondagaon craft cluster", issue_type="Craft Decline",
        description="Only a handful of elderly artisans remain practicing this terracotta technique. "
                     "No younger practitioners are taking it up, and there is a lack of documentation "
                     "of the traditional methods before they are lost.",
        reported_severity="High",
    ),
}


def render_demo_mode():
    hero_header("DEMO MODE", "One-click end-to-end simulation of the full workflow for judges.", "")
    prototype_disclaimer("Demo Mode creates a real demo report in the local database and runs it through the entire workflow automatically.")

    scenario = st.selectbox("Choose a demo scenario", list(DEMO_SCENARIOS.keys()))
    use_ai = st.checkbox("Use AI-assisted analysis (Ollama / Phi-3) if available", value=True, key="demo_use_ai")

    if st.button("▶ Run Demo", use_container_width=True):
        data = DEMO_SCENARIOS[scenario]
        progress = st.progress(0, text="Submitting report...")

        result = report_service.create_report(
            heritage_name=data["heritage_name"], heritage_type=data["heritage_type"],
            state=data["state"], district=data["district"], location=data["location"],
            description=data["description"], issue_type=data["issue_type"],
            reported_severity=data["reported_severity"], date_observed=str(date.today()),
            image_path="", use_ai=use_ai,
        )
        report_id = result["report_id"]
        progress.progress(20, text="AI preliminary risk assessment complete...")

        verification_service.submit_verification(report_id, "Dr. Verifier (Demo)", "VERIFIED", "Confirmed on-site condition matches report (demo).")
        progress.progress(40, text="Verified by heritage expert...")

        alert = alert_service.maybe_create_alert(report_id)
        progress.progress(55, text="Alert routing to prototype organization..." if alert else "Risk below alert threshold, skipping alert...")

        org = monitoring_service.assign_case(report_id, "Auto-assigned via Demo Mode")
        progress.progress(70, text=f"Assigned to {org['name']}...")
        monitoring_service.schedule_inspection(report_id, "Demo: inspection scheduled")
        monitoring_service.mark_in_progress(report_id, "Demo: conservation work underway")
        monitoring_service.mark_resolved(report_id, "Demo: initial intervention complete")
        progress.progress(85, text="Action workflow complete...")

        assessment = report_service.get_latest_assessment(report_id)
        start_score = assessment.get("score", 80)
        monitoring_service.move_to_monitoring(report_id, condition="Improving", notes="Demo: post-intervention monitoring begins")
        for score, cond in [(max(0, start_score - 20), "Improving"), (max(0, start_score - 45), "Stable")]:
            monitoring_service.add_monitoring_update(report_id, score, cond, "Simulated monitoring trend", "")
        progress.progress(100, text="Monitoring trend simulated.")

        st.success(f"Demo complete for **{data['heritage_name']}** — Report ID `{report_id}`")
        st.session_state.view_report_id = report_id
        st.balloons()
        if st.button("View Full Case File →", key="demo_view_case"):
            st.session_state.page = "🧠 AI Risk Assessment"
            st.rerun()
