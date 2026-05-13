from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StoryArc(BaseModel):
    title: str
    description: str


class RecurringPerson(BaseModel):
    identifier: str
    context: str


class DefiningMoment(BaseModel):
    moment: str
    significance: str


class MindsetShift(BaseModel):
    from_state: str = Field(alias="from")
    to_state: str = Field(alias="to")
    evidence: str
    period: str


class IdentityContradiction(BaseModel):
    observation: str
    evidence: str
    interpretation: str


class GemmaLoreOutput(BaseModel):
    """Validates Gemma 4's JSON response before storage."""

    the_sentence: str
    narrative: str
    story_arcs: list[StoryArc]
    recurring_people: list[RecurringPerson]
    defining_moments: list[DefiningMoment]
    mindset_shifts: list[MindsetShift]
    core_themes: list[str]
    identity_contradictions: list[IdentityContradiction]


class LoreSnapshot(BaseModel):
    id: str
    run_id: str
    the_sentence: str
    narrative: str
    story_arcs: list[StoryArc]
    recurring_people: list[RecurringPerson]
    defining_moments: list[DefiningMoment]
    mindset_shifts: list[MindsetShift]
    core_themes: list[str]
    identity_contradictions: list[IdentityContradiction]
    created_at: str
    run_triggered_at: str
    file_count: int


class LoreSnapshotListItem(BaseModel):
    id: str
    run_id: str
    the_sentence: str
    created_at: str
    status: str


class LoreSnapshotList(BaseModel):
    snapshots: list[LoreSnapshotListItem]
    total: int


class DiffRequest(BaseModel):
    snapshot_id_a: str
    snapshot_id_b: str


class LoreDiff(BaseModel):
    sentence_a: str
    sentence_b: str
    narrative_diff: str
    themes_added: list[str]
    themes_removed: list[str]
    new_people: list[str]
    dropped_people: list[str]
