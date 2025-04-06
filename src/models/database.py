from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    slack_user_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    paraphrases = relationship("Paraphrase", back_populates="user")

class Paraphrase(Base):
    __tablename__ = "paraphrases"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text)
    paraphrased_text = Column(Text)
    tone = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="paraphrases") 