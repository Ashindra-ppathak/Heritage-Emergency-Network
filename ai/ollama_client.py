"""
Local Ollama client for Heritage Emergency Network.

This module talks to a locally running Ollama instance (http://localhost:11434)
using the phi3 model by default. If Ollama is not running or the model is not
available, every function degrades gracefully so the rest of the application
keeps working with the deterministic fallback engine.
"""

import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"
TIMEOUT_SECONDS = 20


def is_ollama_available() -> bool:
    """Check whether a local Ollama server is reachable."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Low-level call to the Ollama /api/generate endpoint.
    Returns the raw text response, or an empty string on failure.
    """
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        return data.get("response", "").strip()
    except Exception:
        return ""


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from model text output."""
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {}


def analyze_report(description: str, issue_type: str, heritage_type: str, severity: str) -> dict:
    """
    Ask Phi-3 to analyze a heritage report and return structured JSON.
    Returns {} if Ollama is unavailable or output could not be parsed —
    callers should fall back to the deterministic rule engine in that case.
    """
    prompt = f"""You are an assistive screening tool for a heritage-risk reporting platform.
You do NOT make final decisions — you only provide preliminary structured analysis for a
human verifier to review.

Heritage type: {heritage_type}
Issue type: {issue_type}
Reporter-observed severity: {severity}
Description: {description}

Respond ONLY with a JSON object, no extra text, in this exact shape:
{{
  "category": "short category label",
  "risk_score": <integer 0-100>,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "key_indicators": ["indicator1", "indicator2"],
  "recommended_priority": "short phrase",
  "reasoning": "1-2 sentence explanation"
}}"""
    raw = _call_ollama(prompt)
    return _extract_json(raw)


def generate_risk_reasoning(report_summary: str) -> str:
    """Generate a short human-readable reasoning paragraph for a report."""
    prompt = f"""Summarize, in 2-3 sentences, why the following heritage report may warrant
attention. Do not declare an official verdict — phrase it as preliminary observations only.

Report: {report_summary}"""
    result = _call_ollama(prompt)
    return result or ""


def generate_recommendation(issue_type: str, risk_level: str) -> str:
    """Generate a short recommended next action."""
    prompt = f"""In one short sentence, recommend a preliminary next action for a heritage
case with issue type "{issue_type}" and preliminary risk level "{risk_level}".
Phrase it as a recommendation for human experts, not a final decision."""
    result = _call_ollama(prompt)
    return result or ""
