import json
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.database import get_db
from src.utils.text import parse_command, get_latest_paraphrase
from src.utils.layout import get_rephrase_result_layout, get_success_layout, get_error_layout
from src.utils.auth import verify_slack_request


router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/rewrite")
async def rewrite(
    request: Request,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        form_data = await request.form()
        logger.info(f"Form data: {form_data}")
        text = form_data.get("text")
        user_id = form_data.get("user_id")

        if not text:
            logger.error(f"No text found in form data for user {user_id}")
            return get_error_layout("Missing text")
        if not user_id:
            logger.error(f"No user_id found in form data for user {user_id}")
            return get_error_layout("Missing user_id")

        # Parse the command to get text and tone
        text_to_rephrase, tone = parse_command(text)

        # Get response_url for sending delayed responses
        response_url = form_data.get("response_url")
        if not response_url:
            logger.error(f"No response_url found in form data for user {user_id}")
            return get_error_layout("Missing response_url")

        # Send immediate acknowledgment
        async with httpx.AsyncClient() as client:
            ack_payload = {
                "response_type": "ephemeral",
                "text": "Rewriting your text, please wait..."
            }
            await client.post(response_url, json=ack_payload)
            logger.info("Sent acknowledgment response")

        # Asynchronously process the rephrase
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(text_to_rephrase, tone)

        if not paraphrased_text:
            logger.error(f"Failed to get paraphrased text from service for user {user_id}")
            return get_error_layout("Failed to paraphrase text")

        # Store in the database with actual user ID
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=text_to_rephrase,
            paraphrased_text=paraphrased_text,
            tone=tone
        )

        # Send the result to Slack
        async with httpx.AsyncClient() as client:
            result_payload = get_rephrase_result_layout(text_to_rephrase, paraphrased_text, user_id)
            await client.post(response_url, json=result_payload)

        return get_success_layout(text_to_rephrase, paraphrased_text, user_id)

    except Exception as e:
        logger.error(f"Error processing rephrase request: {str(e)}")
        return get_error_layout("Error processing request")


@router.post("/rewrite-action")
async def rewrite_action(
    request: Request,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        return get_error_layout("Unauthorized")
    
    try:
        form_data = await request.form()
        payload = form_data.get("payload")
        if not payload:
            logger.error("No payload found in form data")
            return get_error_layout("Missing payload")
            
        payload_data = json.loads(payload)
        user_id = payload_data["user"]["id"]
        response_url = payload_data["response_url"]
        action_id = payload_data["actions"][0]["action_id"]
    
        # Send immediate acknowledgment
        async with httpx.AsyncClient() as client:
            ack_payload = {
                "response_type": "ephemeral",
                "text": "Processing your request..."
            }
            await client.post(response_url, json=ack_payload)

        # Get or create user and fetch their latest paraphrase
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)

        # Get the latest paraphrase for this user
        latest_paraphrases = db_service.get_user_paraphrases(user.id, limit=1)
        if not latest_paraphrases:
            logger.error("No previous paraphrases found for user")
            return get_error_layout("No previous text to rephrase")

        original_text, paraphrased_text = get_latest_paraphrase(latest_paraphrases)
   
        if action_id == "rewrite_button":    
            logger.info("Received rewrite_button action")
            # Get new paraphrased text
            paraphrase_service = ParaphraseService()
            new_paraphrased_text = await paraphrase_service.paraphrase(original_text)
            
            if not new_paraphrased_text:
                logger.error("Failed to get paraphrased text")
                return get_error_layout("Failed to paraphrase text")
            
            # Store new paraphrase in database
            db_service.create_paraphrase(
                user_id=user.id,
                original_text=original_text,
                paraphrased_text=new_paraphrased_text,
                tone=None
            )
            
            # Send the result to Slack
            async with httpx.AsyncClient() as client:
                result_payload = get_rephrase_result_layout(original_text, new_paraphrased_text, user_id)
                await client.post(response_url, json=result_payload)
            
            return {}

        elif action_id == "copy_button":
            logger.info("Received copy_button action")
            # Send a message with just the paraphrased text for easy copying
            async with httpx.AsyncClient() as client:
                copy_payload = {
                    "response_type": "ephemeral",
                    "text": paraphrased_text
                }
                await client.post(response_url, json=copy_payload)
            return {}

    except Exception as e:
        logger.error(f"Error processing rephrase action: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")


