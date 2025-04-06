from sqlalchemy.orm import Session
from src.models.database import User, Paraphrase
from typing import Optional

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, slack_user_id: str) -> User:
        user = self.db.query(User).filter(User.slack_user_id == slack_user_id).first()
        if not user:
            user = User(slack_user_id=slack_user_id)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_paraphrase(
        self,
        user_id: int,
        original_text: str,
        paraphrased_text: str,
        tone: Optional[str] = None
    ) -> Paraphrase:
        paraphrase = Paraphrase(
            user_id=user_id,
            original_text=original_text,
            paraphrased_text=paraphrased_text,
            tone=tone
        )
        self.db.add(paraphrase)
        self.db.commit()
        self.db.refresh(paraphrase)
        return paraphrase

    def get_user_paraphrases(self, user_id: int, limit: int = 10) -> list[Paraphrase]:
        return (
            self.db.query(Paraphrase)
            .filter(Paraphrase.user_id == user_id)
            .order_by(Paraphrase.created_at.desc())
            .limit(limit)
            .all()
        ) 