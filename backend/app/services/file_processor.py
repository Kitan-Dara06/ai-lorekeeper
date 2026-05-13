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

MODAL_DESCRIBE_URL = (
    "https://ololadeaaliyah--ai-lorekeeper-gemma-serve.modal.run/v1/describe-image"
)


async def describe_image_via_gemma(file_path: str) -> Optional[str]:
    """Send image to Gemma 4 on Modal for a detailed description."""
    try:
        with open(file_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                MODAL_DESCRIBE_URL,
                json={
                    "image_base64": img_b64,
                    "prompt": "Describe this image in detail. Read any visible text. What story does this image tell about this person's life?",
                },
            )
            if response.status_code == 200:
                desc = response.json().get("description", "")
                if desc:
                    return f"[Image description from AI: {desc}]"
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
