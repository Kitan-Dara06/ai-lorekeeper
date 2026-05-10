import csv
import io
import json
import os
import re
import uuid
from datetime import datetime
from typing import Optional

from PIL import Image

from app.config import settings


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz

    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_text_from_md(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_text_from_json(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)


def extract_text_from_csv(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = [", ".join(row) for row in reader]
    return "\n".join(rows)


def extract_text_from_image(file_path: str) -> Optional[str]:
    """Extract metadata and description from image. Actual OCR not performed in MVP."""
    try:
        img = Image.open(file_path)
        info = {
            "format": img.format,
            "size": f"{img.width}x{img.height}",
            "mode": img.mode,
        }
        exif_data = img._getexif() if hasattr(img, "_getexif") else None
        if exif_data:
            info["exif"] = str(exif_data)
        return f"[Image: {json.dumps(info)}]"
    except Exception:
        return f"[Image file: {os.path.basename(file_path)}]"


def extract_text(file_path: str, file_type: str) -> Optional[str]:
    """Extract text content from a file based on its type."""
    extractors = {
        "pdf": extract_text_from_pdf,
        "txt": extract_text_from_txt,
        "md": extract_text_from_md,
        "json": extract_text_from_json,
        "csv": extract_text_from_csv,
        "jpg": extract_text_from_image,
        "jpeg": extract_text_from_image,
        "png": extract_text_from_image,
        "webp": extract_text_from_image,
    }
    extractor = extractors.get(file_type.lower())
    if extractor:
        try:
            return extractor(file_path)
        except Exception as e:
            return f"[Error extracting text: {str(e)}]"
    return None


def infer_period_from_filename(
    filename: str,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Try to infer a date period from common filename patterns."""
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
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext if ext else "unknown"


ALLOWED_TYPES = {"txt", "pdf", "md", "json", "csv", "jpg", "jpeg", "png", "webp"}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
