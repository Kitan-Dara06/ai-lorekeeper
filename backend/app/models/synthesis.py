import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.database import Base


class SynthesisRun(Base):
    __tablename__ = "synthesis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    triggered_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, running, completed, failed
