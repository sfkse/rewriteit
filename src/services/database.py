from sqlalchemy.orm import Session
from src.models.database import User, Paraphrase
from src.utils.constants import FREE_CREDITS
from typing import Optional, Dict, Any

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, slack_user_id: str, user_name: str = None, user_info: Dict[str, Any] = None) -> User:
        user = self.db.query(User).filter(User.slack_user_id == slack_user_id).first()
        if not user:
            user = User(
                slack_user_id=slack_user_id,
                user_name=user_name,
                credits_assigned=FREE_CREDITS,
                user_info=user_info
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        else:
            # Update existing user's info
            if user_name:
                user.user_name = user_name
            if user_info:
                user.user_info = user_info
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_user_credits(self, user_id: int):
        user = self.db.query(User).filter(User.id == user_id).first()
        user.credits_used += 1
        self.db.commit()
        self.db.refresh(user)

    def create_or_update_paraphrase(
        self,
        user_id: int,
        original_text: str,
        paraphrased_text: str,
        tone: Optional[str] = None
    ) -> Paraphrase:
        paraphrase = self.db.query(Paraphrase).filter(Paraphrase.user_id == user_id).order_by(Paraphrase.created_at.desc()).first()
        if not paraphrase:
            paraphrase = Paraphrase(
                user_id=user_id,
                original_text=original_text,
                paraphrased_text=paraphrased_text,
                tone=tone
            )
            self.db.add(paraphrase)
        else:
            paraphrase.original_text = original_text
            paraphrase.paraphrased_text = paraphrased_text
            paraphrase.tone = tone
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
    
    def delete_user_paraphrases(self, user_id: int):
        user = self.get_or_create_user(user_id)
        # Get the IDs of paraphrases to keep (latest 10)
        keep_ids = (
            self.db.query(Paraphrase.id)
            .filter(Paraphrase.user_id == user.id)
            .order_by(Paraphrase.created_at.desc())
            .limit(10)
            .subquery()
        )
        # Delete all paraphrases except the ones to keep
        self.db.query(Paraphrase).filter(
            Paraphrase.user_id == user.id,
            ~Paraphrase.id.in_(self.db.query(keep_ids))
        ).delete(synchronize_session=False)
        self.db.commit()