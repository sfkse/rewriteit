from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.slack import SlackPayload
from src.models.paraphrase import ParaphraseRequest, ParaphraseResponse
from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/rephrase", response_model=ParaphraseResponse)
async def rephrase(
    request: ParaphraseRequest,
    db: Session = Depends(get_db)
):
    try:
        # Get or create user
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(request.user_id)
        
        # Get paraphrased text
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(request.text, request.tone)
        
        # Store in database
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=request.text,
            paraphrased_text=paraphrased_text,
            tone=request.tone
        )
        
        return ParaphraseResponse(text=paraphrased_text)
    except Exception as e:
        logger.error(f"Error processing rephrase request: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request")

@router.post("/rephrase_action")
async def rephrase_action(
    payload: SlackPayload,
    db: Session = Depends(get_db)
):
    try:
        # Get or create user
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(payload.user.id)
        
        # Get paraphrased text
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(
            payload.actions[0].value,
            payload.actions[0].name if payload.actions[0].name != "default" else None
        )
        
        # Store in database
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=payload.actions[0].value,
            paraphrased_text=paraphrased_text,
            tone=payload.actions[0].name if payload.actions[0].name != "default" else None
        )
        
        # Return success response
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing rephrase action: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request") 
