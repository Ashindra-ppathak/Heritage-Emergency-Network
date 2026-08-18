# Heritage Emergency Network

**"Protect Heritage Before It Is Lost."**

An AI-assisted early-warning and coordination platform for Indian cultural heritage at risk —
built as a local-first Streamlit prototype for a college Project Expo.

---

## 1. Problem Statement

India's cultural heritage — monuments, temples, forts, stepwells, traditional crafts, folk
traditions, and festivals — is continuously threatened by neglect, environmental damage,
vandalism, illegal encroachment, natural disasters, and the quiet disappearance of intangible
traditions (declining practitioners, loss of documentation, community displacement). Citizen
observations of these risks are scattered, undocumented, and rarely reach the right people
before damage becomes irreversible.

## 2. Solution

Heritage Emergency Network turns scattered citizen reports into structured, prioritized
heritage-risk cases through a single, transparent workflow:

```
REPORT → AI SCREEN → VERIFY → ALERT → ACT → MONITOR
```

Citizens report a site or tradition at risk (photo, location, description). The system runs an
**AI-assisted preliminary risk assessment** (not an official verdict). A human **Heritage
Expert / Verifier** reviews and confirms or rejects the case. Verified high-risk cases generate
an **alert** routed to a simulated **Authority / Organization**, which can assign, inspect, act
on, and eventually resolve the case. Resolved cases move into **Monitoring**, where risk trends
are tracked over time.

## 3. Core Workflow

```
[✓ REPORT] → [✓ AI SCREEN] → [● VERIFY] → [○ ALERT] → [○ ACT] → [○ MONITOR]
```

This tracker is shown on every case throughout the application.

## 4. Key Features

- **Citizen reporting** — photo, location, heritage type, issue type, description, severity.
- **AI preliminary risk assessment** — score (0–100), risk level, reasons, recommended priority.
  Clearly labeled as *preliminary screening*, never an official verdict.
- **Human verification workflow** — a verifier must Verify / Reject / Request More Evidence.
  AI never has final authority.
- **Automatic alerting** — verified cases with risk ≥ 75 generate a high-priority alert.
- **Prototype organization routing** — cases are routed to a simulated authority based on
  issue type (clearly labeled as demo entities, not real institutions).
- **Authority action workflow** — Assign → Schedule Inspection → Action In Progress →
  Resolved → Monitoring.
- **Monitoring & risk trend** — simulated risk-score history with charts.
- **Heritage Risk Map** — India-wide scatter map of reported cases, colored by risk.
- **Analytics dashboard** — reports by state/type, risk distribution, verification rate, etc.
- **Intangible heritage support** — crafts, folk traditions, and festivals are first-class
  categories with their own risk factors (declining practitioners, commercialization pressure,
  loss of documentation).
- **Demo Mode** — one-click, end-to-end scenario simulation for judges.
- **Role simulation** — Citizen / Verifier / Authority / Admin (prototype only, no real auth).
- **Graceful AI fallback** — if Ollama isn't running, a deterministic rule-based risk engine
  takes over automatically. The app always works.

## 5. Architecture

```
heritage-emergency-network/
│
├── app.py                     # Streamlit entry point, sidebar, routing
├── requirements.txt
├── README.md
├── .gitignore
│
├── database/
│   └── heritage.db            # SQLite (auto-created on first run)
│
├── data/
│   ├── heritage_sites.json    # States + sample heritage sites
│   ├── risk_rules.json        # Deterministic fallback scoring rules
│   ├── issue_types.json       # Issue types, heritage types, severities
│   └── organizations.json     # Prototype routing organizations
│
├── ai/
│   ├── ollama_client.py       # Local Ollama (Phi-3) HTTP client
│   ├── risk_assessor.py       # AI + fallback risk scoring engine
│   ├── report_analyzer.py     # Description/keyword/urgency analysis
│   └── recommendation_engine.py  # Recommended actions + org routing
│
├── services/
│   ├── report_service.py      # Report CRUD + triggers AI assessment
│   ├── verification_service.py
│   ├── alert_service.py
│   ├── monitoring_service.py  # Also handles Authority Action (ACT stage)
│   └── analytics_service.py
│
├── utils/
│   ├── database.py            # SQLite connection + schema
│   ├── helpers.py             # IDs, risk levels, formatting
│   └── image_utils.py         # Image saving + lightweight heuristics
│
├── ui/
│   ├── styles.py               # Premium dark theme CSS
│   ├── components.py           # Reusable widgets (badges, workflow tracker, etc.)
│   └── pages.py                # All page render functions
│
└── assets/
    └── logo.png
```

## 6. Tech Stack

| Layer     | Technology                     |
|-----------|---------------------------------|
| Frontend  | Streamlit                       |
| Backend   | Python                          |
| Database  | SQLite (local file, auto-init)  |
| AI        | Local Ollama + Phi-3 (optional) |
| Charts    | Plotly                          |
| Images    | Pillow                          |

No paid APIs. No mandatory cloud dependency. Everything runs on `localhost`.

## 7. The Role of AI

Phi-3 (via a local Ollama server) is used **only** for preliminary, assistive screening:

1. Understanding the report description
2. Summarizing the issue
3. Identifying potential risk indicators
4. Recommending a preliminary next action
5. Generating structured reasoning (risk score, level, key indicators)

**AI does NOT:**
- Declare a monument officially endangered
- Replace human experts or authorities
- Send real government notices
- Make the final verification decision

If Ollama is not running, `ai/risk_assessor.py` automatically falls back to a deterministic,
rule-based engine (`data/risk_rules.json`) so the prototype **always** produces a score and
never breaks the demo.

Every AI output in the UI is labeled:
> ⚠️ **AI Preliminary Assessment** — For screening and prioritization only. Final verification
> requires qualified human review.

## 8. Database Schema

`users`, `reports`, `risk_assessments`, `verifications`, `alerts`, `actions`, `monitoring` —
see `utils/database.py` for full column definitions. The schema is created automatically the
first time the app runs (`init_db()` is called at the top of `app.py`).

## 9. Installation (Windows)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Optional: enable local AI (Ollama + Phi-3)

1. Install Ollama: https://ollama.com/download
2. Pull the model:
   ```bat
   ollama pull phi3
   ```
3. Make sure Ollama is running (it starts a local server at `http://localhost:11434`).

If you skip this step entirely, the app still works — it just uses the deterministic fallback
risk engine instead of Phi-3.

## 10. Run the App

```bat
streamlit run app.py
```

Then open: **http://localhost:8501**

## 11. Demo Flow for Judges (~3 minutes)

1. Open the **Dashboard**.
2. Click **"Report Heritage at Risk"**.
3. Upload a sample photo (optional) and fill in heritage details.
4. Submit the report → a **Report ID** (e.g. `HEN-2026-00127`) is generated instantly.
5. The **AI Preliminary Risk Assessment** appears (score, level, reasons).
6. Go to **Verification** → review and click **Verify**.
7. The system automatically creates a **🚨 High Priority Alert** (if risk ≥ 75) and routes it
   to a prototype organization — see the **Alerts** page.
8. Go to **Authority Action** → Assign Team → Schedule Inspection → Mark Resolved.
9. Move the case to **Monitoring** and watch the simulated risk trend improve
   (e.g. `87 → 62 → 35`).
10. Open **Heritage Risk Map** and **Analytics** to show the aggregate view.

**Shortcut:** toggle **🎬 Demo Mode** in the sidebar and click **Run Demo** to execute this
entire flow automatically in one click, for either a structural-damage scenario or an
intangible-heritage (craft decline) scenario.

## 12. Troubleshooting

| Issue | Fix |
|---|---|
| `streamlit: command not found` | Activate the venv first, or run `python -m streamlit run app.py`. |
| Blank / broken charts | Ensure `plotly` installed correctly: `pip install plotly`. |
| AI status shows "Offline" | Ollama isn't running or `phi3` isn't pulled — this is expected and fine; the app still works via fallback. |
| Database looks stale / want a fresh demo | Delete `database/heritage.db` and restart the app — it will recreate an empty schema. |
| Port already in use | Run `streamlit run app.py --server.port 8502`. |

## 13. Honesty & Scope Notes (Important)

- Organizations listed (Heritage Conservation Cell, Archaeological Authority, etc.) are
  **prototype/demo entities only** — there is **no real government integration**.
- AI provides **preliminary screening and prioritization**, not a scientific structural safety
  determination or official heritage certification.
- The Heritage Risk Map uses **approximate, jittered state-level coordinates** for
  visualization — it is not a survey-grade GIS tool.
- All demo data (sample reports, organizations, states) is fictional/illustrative and does not
  represent live, official cases.

## 14. Future Scope

- Official authority / government system integrations
- Verified GIS data and satellite imagery-based change detection
- Real image-based computer-vision damage detection
- Multilingual reporting (Hindi + regional languages)
- Expert reviewer networks with credentialing
- Community heritage archives
- Real-time disaster-linked alerts
- Mobile application

---

*Heritage Emergency Network is a Project Expo prototype. It demonstrates an architecture for
AI-assisted early warning and human-led verification/action for heritage at risk — it is not a
production system and makes no claims of official government partnership.*
