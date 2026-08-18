"""
Image utility functions for handling uploaded heritage photos.
"""

import os
import uuid
from PIL import Image

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "uploads"
)


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_image(uploaded_file, report_id: str) -> str:
    """
    Save a Streamlit UploadedFile to disk and return the relative path.
    Returns empty string if no file was provided or saving fails.
    """
    if uploaded_file is None:
        return ""
    ensure_upload_dir()
    try:
        ext = os.path.splitext(uploaded_file.name)[1] or ".jpg"
        filename = f"{report_id}_{uuid.uuid4().hex[:6]}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        image = Image.open(uploaded_file)
        image = image.convert("RGB")
        # Downscale large images to keep the prototype lightweight
        image.thumbnail((1200, 1200))
        image.save(filepath, format="JPEG", quality=85)
        return filepath
    except Exception:
        return ""


def image_exists(path: str) -> bool:
    return bool(path) and os.path.exists(path)


def basic_damage_indicators(image_path: str) -> list:
    """
    Very lightweight heuristic 'visual indicator' placeholder.
    This does NOT perform real computer-vision damage detection —
    it is a deterministic stand-in used only when no AI model is available,
    so the prototype can still show an illustrative indicator.
    """
    if not image_exists(image_path):
        return []
    try:
        img = Image.open(image_path).convert("L")  # grayscale
        # crude brightness/contrast based heuristic - illustrative only
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        indicators = []
        if avg < 90:
            indicators.append("Low-light / shadowed image (possible poor site condition)")
        if avg > 210:
            indicators.append("Overexposed image (visual assessment may be limited)")
        return indicators
    except Exception:
        return []
