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
    UUID,
    ENUM
)

from src.core.db import Base
from src.core.enums import (
    PipelineStatus,
    FollowUpType,
    LeadStatus
)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    company = Column(String(128), nullable=True)
    phone_number = Column(String(17), nullable=False)
    email = Column(String(128), nullable=False)

    pipeline_status = Column(
        ENUM(PipelineStatus),
        nullable=False,
        default=PipelineStatus.NEW
    )

    lead_status = Column(ENUM(LeadStatus), nullable=False)

    created_at = Column(DateTime, default=func.now(), index=True, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    owner = relationship("User", back_populates="leads")
    notes = relationship("Note", back_populates="lead")