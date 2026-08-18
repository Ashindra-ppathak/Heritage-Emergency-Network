"""
Premium dark theme CSS for Heritage Emergency Network.
"""

COLORS = {
    "bg": "#070B14",
    "panel": "#0F1626",
    "card": "#111A2E",
    "border": "#24324A",
    "primary": "#5B8CFF",
    "secondary": "#8B5CF6",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "critical": "#EF4444",
    "text": "#F8FAFC",
    "text_secondary": "#94A3B8",
}


def inject_css():
    return f"""
    <style>
    .stApp {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
    }}
    [data-testid="stSidebar"] {{
        background-color: {COLORS['panel']};
        border-right: 1px solid {COLORS['border']};
    }}
    [data-testid="stSidebar"] * {{
        color: {COLORS['text']} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS['text']} !important;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        letter-spacing: 0.3px;
    }}
    p, span, label, div {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }}
    .hen-hero {{
        background: linear-gradient(135deg, {COLORS['panel']} 0%, {COLORS['card']} 100%);
        border: 1px solid {COLORS['border']};
        border-radius: 18px;
        padding: 36px 32px;
        margin-bottom: 24px;
        box-shadow: 0 0 40px rgba(91,140,255,0.08);
    }}
    .hen-title {{
        font-size: 34px;
        font-weight: 800;
        color: {COLORS['text']};
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }}
    .hen-tagline {{
        font-size: 17px;
        color: {COLORS['primary']};
        font-weight: 600;
        margin-bottom: 10px;
    }}
    .hen-subtext {{
        color: {COLORS['text_secondary']};
        font-size: 14px;
        max-width: 700px;
    }}
    .hen-card {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 14px;
    }}
    .hen-metric-value {{
        font-size: 30px;
        font-weight: 800;
        color: {COLORS['primary']};
    }}
    .hen-metric-label {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }}
    .hen-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    .badge-low {{ background: rgba(34,197,94,0.15); color: {COLORS['success']}; border: 1px solid {COLORS['success']}; }}
    .badge-medium {{ background: rgba(245,158,11,0.15); color: {COLORS['warning']}; border: 1px solid {COLORS['warning']}; }}
    .badge-high {{ background: rgba(251,146,60,0.15); color: #FB923C; border: 1px solid #FB923C; }}
    .badge-critical {{ background: rgba(239,68,68,0.15); color: {COLORS['critical']}; border: 1px solid {COLORS['critical']}; }}
    .hen-disclaimer {{
        background: rgba(139,92,246,0.08);
        border-left: 3px solid {COLORS['secondary']};
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 12.5px;
        color: {COLORS['text_secondary']};
        margin: 10px 0;
    }}
    .hen-workflow-step {{
        display: inline-block;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
        background: {COLORS['card']};
        font-size: 13px;
        font-weight: 600;
        color: {COLORS['text_secondary']};
        margin-right: 6px;
    }}
    .hen-workflow-step.done {{
        border-color: {COLORS['success']};
        color: {COLORS['success']};
        background: rgba(34,197,94,0.08);
    }}
    .hen-workflow-step.active {{
        border-color: {COLORS['primary']};
        color: {COLORS['primary']};
        background: rgba(91,140,255,0.1);
    }}
    .stButton > button {{
        background-color: {COLORS['primary']};
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 8px 18px;
    }}
    .stButton > button:hover {{
        background-color: #4A78E0;
        color: white;
    }}
    hr {{
        border-color: {COLORS['border']};
    }}
    </style>
    """
