import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class LoreOutput(Base):
    __tablename__ = "lore_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("synthesis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    the_sentence = Column(Text, nullable=False)
    narrative = Column(Text, nullable=False)
    story_arcs = Column(Text, nullable=False)  # JSON string
    recurring_people = Column(Text, nullable=False)  # JSON string
    defining_moments = Column(Text, nullable=False)  # JSON string
    mindset_shifts = Column(Text, nullable=False)  # JSON string
    core_themes = Column(Text, nullable=False)  # JSON string
    identity_contradictions = Column(Text, nullable=False)  # JSON string
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
