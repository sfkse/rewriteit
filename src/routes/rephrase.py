import json
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.services.slack import SlackService
from src.utils.text import parse_command, get_latest_paraphrase
from src.utils.layout import get_rephrase_response_layout, get_processing_layout, get_error_layout, get_acknowledgment_layout
from src.utils.auth import verify_slack_request
from src.database import get_db     

router = APIRouter()
logger = logging.getLogger(__name__)

# Background task function for processing paraphrasing
async def process_paraphrase_task(
    text_to_rephrase: str,
    tone: str,
    user_id: str,
    response_url: str,
    db_session: Session
):
    try:
        # Get a new database session for this background task
        db = db_session
        
        # Process the rephrase request asynchronously
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(text_to_rephrase, tone)
        
        if not paraphrased_text:
            logger.error(f"Failed to get paraphrased text from service for user {user_id}")
            # Send error response
            slack_service = SlackService()
            error_layout = get_error_layout("Failed to paraphrase text")
            await slack_service.send_action_response(response_url, error_layout)
            return
        
        # Store in the database
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=text_to_rephrase,
            paraphrased_text=paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        slack_service = SlackService()
        rephrased_layout = get_rephrase_response_layout(text_to_rephrase, paraphrased_text, user_id)
        await slack_service.send_action_response(response_url, rephrased_layout)
        logger.info(f"Successfully processed paraphrase for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in background paraphrase task: {str(e)}", exc_info=True)
        # Send error to user
        slack_service = SlackService()
        error_layout = get_error_layout("Error processing your request")
        await slack_service.send_action_response(response_url, error_layout)

# Background task function for processing rewrite action
async def process_rewrite_action_task(
    original_text: str,
    user_id: str,
    response_url: str,
    db_session: Session,
    tone: str | None = None
):
    try:
        # Get a new database session for this background task
        db = db_session
        
        # Get new paraphrased text
        paraphrase_service = ParaphraseService()
        new_paraphrased_text = await paraphrase_service.paraphrase(original_text, tone)
        
        if not new_paraphrased_text:
            logger.error(f"Failed to get paraphrased text for user {user_id}")
            # Send error response
            slack_service = SlackService()
            error_layout = get_error_layout("Failed to paraphrase text")
            await slack_service.send_action_response(response_url, error_layout)
            return
        
        # Store new paraphrase in database
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=original_text,
            paraphrased_text=new_paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        slack_service = SlackService()
        rephrased_layout = get_rephrase_response_layout(original_text, new_paraphrased_text, user_id)
        await slack_service.send_action_response(response_url, rephrased_layout)
        logger.info(f"Successfully processed rewrite action for user {user_id}")

        # Delete all user paraphrases
        db_service.delete_user_paraphrases(user_id)
    
    except Exception as e:
        logger.error(f"Error in background rewrite action task: {str(e)}", exc_info=True)
        # Send error to user
        slack_service = SlackService()
        error_layout = get_error_layout("Error processing your request")
        await slack_service.send_action_response(response_url, error_layout)

@router.post("/rewrite")
async def rewrite(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Get form data and validate essential fields
        form_data = await request.form()
        text = form_data.get("text")
        user_id = form_data.get("user_id")
        response_url = form_data.get("response_url")
        
        # Validate request data
        if not text:
            logger.error(f"No text found in form data for user {user_id}")
            return get_error_layout("Missing text")
        if not user_id:
            logger.error(f"No user_id found in form data for user {user_id}")
            return get_error_layout("Missing user_id")
        if not response_url:
            logger.error(f"No response_url found in form data for user {user_id}")
            return get_error_layout("Missing response_url")
            
        # Parse the command to get text and tone
        text_to_rephrase, tone = parse_command(text)
        
        # Send acknowledgment via response_url (Slack will already have received this)
        slack_service = SlackService()
        acknowledgment_layout = get_acknowledgment_layout(user_id)
        await slack_service.send_action_response(response_url, acknowledgment_layout)
        
        # Add background task to do the actual work
        background_tasks.add_task(
            process_paraphrase_task,
            text_to_rephrase=text_to_rephrase,
            tone=tone, 
            user_id=user_id,
            response_url=response_url,
            db_session=db
        )
        
        # Return an immediate response (within 3 seconds) to Slack
        logger.info(f"Added paraphrase task to background for user {user_id}")
        return get_processing_layout()
        
    except Exception as e:
        logger.error(f"Error processing rephrase request: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")

@router.post("/rewrite-action")
async def rewrite_action(
    request: Request,
    background_tasks: BackgroundTasks,
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
        slack_service = SlackService()
        acknowledgment_layout = get_acknowledgment_layout(user_id)
        await slack_service.send_action_response(response_url, acknowledgment_layout)
        
        if action_id == "rewrite_button":
            logger.info("Received rewrite_button action")
            
            # Get the latest paraphrase for this user
            db_service = DatabaseService(db)
            user = db_service.get_or_create_user(user_id)
            latest_paraphrases = db_service.get_user_paraphrases(user.id, limit=1)
            
            if not latest_paraphrases:
                logger.error("No previous paraphrases found for user")
                return get_error_layout("No previous text to rephrase")
                
            original_text, _ = get_latest_paraphrase(latest_paraphrases)
            
            # Get tone from input if provided
            logger.info(f"Payload data: {payload_data}")
            tone = None
            if "state" in payload_data and "values" in payload_data["state"]:
                tone_block = payload_data["state"]["values"].get("tone_input_block", {})
                if "tone_input" in tone_block:
                    tone = tone_block["tone_input"]["value"]
                    if tone:
                        tone = tone.strip()
            
            # Add background task to process the rewrite
            background_tasks.add_task(
                process_rewrite_action_task,
                original_text=original_text,
                user_id=user_id,
                response_url=response_url,
                db_session=db,
                tone=tone
            )
            
            # Return immediate response
            return {}
            
        elif action_id == "copy_button":
            logger.info("Received copy_button action")
            # Get the latest paraphrase for this user
            db_service = DatabaseService(db)
            user = db_service.get_or_create_user(user_id)
            latest_paraphrases = db_service.get_user_paraphrases(user.id, limit=1)
            
            if not latest_paraphrases:
                logger.error("No previous paraphrases found for user")
                return get_error_layout("No previous text to rephrase")
                
            _, paraphrased_text = get_latest_paraphrase(latest_paraphrases)
            
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
