from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slack_user_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    paraphrases = relationship("Paraphrase", back_populates="user")

class Paraphrase(Base):
    __tablename__ = "paraphrases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_text = Column(Text, nullable=False)
    paraphrased_text = Column(Text, nullable=False)
    tone = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="paraphrases") 