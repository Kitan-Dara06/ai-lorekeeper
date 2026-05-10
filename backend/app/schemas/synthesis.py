from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TriggerSynthesisRequest(BaseModel):
    file_ids: Optional[list[str]] = None  # None means all files


class SynthesisRunInfo(BaseModel):
    id: str
    file_count: int
    triggered_at: str
    status: str


class SynthesisRunList(BaseModel):
    runs: list[SynthesisRunInfo]
    total: int
