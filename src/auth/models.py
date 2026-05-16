import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    func

)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM

from src.core.db import Base
from src.core.enums import LoginMethod

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    name = Column(String(64), nullable=False)
    email = Column(String(64), unique=True, nullable=False)
    password = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(), default=func.now(), index=True, nullable=False)
    updated_at = Column(DateTime(), default=func.now(), nullable=False, server_onupdate=func.now())
    login_method = Column(ENUM(LoginMethod),nullable=False)
    