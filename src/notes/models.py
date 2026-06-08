import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    func,
)

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
    ENUM
)

from src.core.db import Base
from src.core.enums import NoteTag

class Note(Base):
    __tablename__ = "notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(1024), nullable=False)

    tags = Column(JSONB(), nullable=True, default=dict)

    created_at = Column(DateTime, default=func.now(), index=True, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    lead = relationship("Lead", back_populates="notes")
    owner = relationship("User", back_populates="notes")