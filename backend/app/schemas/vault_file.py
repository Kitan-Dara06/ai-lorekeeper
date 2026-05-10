from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    source_tag: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    uploaded_at: str


class FileListItem(BaseModel):
    id: str
    filename: str
    file_type: str
    source_tag: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    uploaded_at: str
    has_extracted_text: bool


class FileListResponse(BaseModel):
    files: list[FileListItem]
    total: int
