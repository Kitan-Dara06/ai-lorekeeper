import base64
import csv
import json
import os
import re
from datetime import datetime
from typing import Optional

import httpx
from PIL import Image

from app.config import settings


async def describe_image_via_gemma(file_path: str) -> Optional[str]:
    """Send image to Gemma 4 via Google AI API for description."""
    if not settings.GEMINI_API_KEY:
        return _extract_image_metadata(file_path)

    try:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode()

        mime = "image/jpeg"
        if file_path.lower().endswith(".png"):
            mime = "image/png"
        elif file_path.lower().endswith(".webp"):
            mime = "image/webp"

        url = f"{settings.GEMINI_API_URL}/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime, "data": img_b64}},
                        {
                            "text": "Describe this image in detail. Read any visible text, names, numbers, or dates. What story does this tell about this person's life?"
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                data = response.json()
                text = ""
                for part in (
                    data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                ):
                    if part.get("text", "").strip():
                        text = part["text"]
                        break
                if text:
                    return f"[Image description from AI: {text.strip()}]"

        return _extract_image_metadata(file_path)
    except Exception:
        return _extract_image_metadata(file_path)


def _extract_image_metadata(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        info = {
            "format": img.format,
            "size": f"{img.width}x{img.height}",
            "mode": img.mode,
        }
        return f"[Image: {json.dumps(info)}]"
    except Exception:
        return f"[Image file: {os.path.basename(file_path)}]"


def extract_text_from_pdf(file_path: str) -> str:
    import fitz

    doc = fitz.open(file_path)
    text_parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_text_from_md(file_path: str) -> str:
    return extract_text_from_txt(file_path)


def extract_text_from_json(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return json.dumps(json.load(f), indent=2)


def extract_text_from_csv(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        return "\n".join([", ".join(row) for row in reader])


async def extract_text(file_path: str, file_type: str) -> Optional[str]:
    """Extract text from a file. Images use Gemma 4 vision; others use direct parsing."""
    if file_type.lower() in ("jpg", "jpeg", "png", "webp"):
        return await describe_image_via_gemma(file_path)
    extractors = {
        "pdf": extract_text_from_pdf,
        "txt": extract_text_from_txt,
        "md": extract_text_from_md,
        "json": extract_text_from_json,
        "csv": extract_text_from_csv,
    }
    extractor = extractors.get(file_type.lower())
    if extractor:
        try:
            return extractor(file_path)
        except Exception as e:
            return f"[Error: {str(e)}]"
    return None


def infer_period_from_filename(
    filename: str,
) -> tuple[Optional[datetime], Optional[datetime]]:
    patterns = [
        (r"(\d{4})-(\d{2})", lambda m: (datetime(int(m[0]), int(m[1]), 1), None)),
        (r"(\d{4})_(\d{2})", lambda m: (datetime(int(m[0]), int(m[1]), 1), None)),
        (
            r"(\d{4})",
            lambda m: (datetime(int(m[0]), 1, 1), datetime(int(m[0]), 12, 31)),
        ),
    ]
    for pattern, factory in patterns:
        match = re.search(pattern, filename)
        if match:
            return factory(match.groups())
    return None, None


def get_file_type(filename: str) -> str:
    return os.path.splitext(filename)[1].lower().lstrip(".") or "unknown"


ALLOWED_TYPES = {"txt", "pdf", "md", "json", "csv", "jpg", "jpeg", "png", "webp"}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
