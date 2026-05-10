import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class VaultFile(Base):
    __tablename__ = "vault_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    source_tag = Column(String(100), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    storage_path = Column(String(1000), nullable=False)
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
