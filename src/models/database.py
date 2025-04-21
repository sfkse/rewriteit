from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime, timezone
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slack_user_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_name = Column(String, nullable=False)
    credits_assigned = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    plan = Column(String, default="free")
    user_info = Column(JSON, nullable=True)
    paraphrases = relationship("Paraphrase", back_populates="user")

class Paraphrase(Base):
    __tablename__ = "paraphrases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_text = Column(Text, nullable=False)
    paraphrased_text = Column(Text, nullable=False)
    tone = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="paraphrases") 