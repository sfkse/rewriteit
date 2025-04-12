import json
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.services.slack import SlackService
from src.utils.text import parse_command, get_latest_paraphrase
from src.utils.request import parse_request
from src.utils.layout import get_rephrase_response_layout, get_processing_layout, get_error_layout, get_acknowledgment_layout
from src.utils.auth import verify_slack_request
from src.database import get_db     

router = APIRouter()
logger = logging.getLogger(__name__)



@router.post("/reword")
async def reword(
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
        text, user_id, user_name, response_url = await parse_request(request)
        slack_service = SlackService()
        
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
        payload = {"response_url": response_url, "user_id": user_id}
        await send_action_response(payload, "acknowledgment", slack_service)
        logger.info(f"Sent acknowledgment to user {user_id}")
        
        # Add background task to do the actual work
        background_tasks.add_task(
            process_paraphrase_task,
            text_to_rephrase=text_to_rephrase,
            tone=tone, 
            user_id=user_id,
            user_name=user_name,
            response_url=response_url,
            db_session=db
        )
        
        # Return an immediate response (within 3 seconds) to Slack
        logger.info(f"Added paraphrase task to background for user {user_id}")
        return get_processing_layout()
        
    except Exception as e:
        logger.error(f"Error processing rephrase request for user {user_id}: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")

@router.post("/reword-action")
async def reword_action(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        return get_error_layout("Unauthorized")
    
    try:
        slack_service = SlackService()
        form_data = await request.form()
        payload = form_data.get("payload")
        if not payload:
            logger.error("No payload found in form data")
            return get_error_layout("Missing payload")
            
        payload_data = json.loads(payload)
        user_id = payload_data["user"]["id"]
        user_name = payload_data["user"]["name"]
        response_url = payload_data["response_url"]
        action_id = payload_data["actions"][0]["action_id"]
    
        # Send immediate acknowledgment
        payload = {"response_url": response_url, "user_id": user_id}
        await send_action_response(payload, "acknowledgment", slack_service)
        logger.info(f"Sent acknowledgment to user {user_id}")
        
        if action_id == "rewrite_button":
            logger.info("Received rewrite_button action")
            
            # Get the latest paraphrase for this user
            db_service = DatabaseService(db)
            user = db_service.get_or_create_user(user_id, user_name)
            latest_paraphrases = db_service.get_user_paraphrases(user.id, limit=1)
            
            if not latest_paraphrases:
                logger.error("No previous paraphrases found for user")
                return get_error_layout("No previous text to rephrase")
                
            original_text, _ = get_latest_paraphrase(latest_paraphrases)
            
            # Get tone from input if provided
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
                user_name=user_name,
                response_url=response_url,
                db_session=db,
                tone=tone
            )
            
            # Return immediate response
            return {}

    except Exception as e:
        logger.error(f"Error processing rephrase action: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")

@router.post("/rewordit-fix")
async def rewordit_fix(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        return get_error_layout("Unauthorized")
    
    try:
        slack_service = SlackService()
        text, user_id, user_name, response_url = await parse_request(request)
        if not text:
            logger.error(f"No text found in form data for user {user_id}")
            return get_error_layout("Missing text")
        if not user_id:
            logger.error(f"No user_id found in form data for user {user_id}")
            return get_error_layout("Missing user_id")
        
        # Send acknowledgment via response_url (Slack will already have received this)
        payload = {"response_url": response_url, "user_id": user_id}
        await send_action_response(payload, "acknowledgment", slack_service)
        logger.info(f"Sent acknowledgment to user {user_id}")
        
        # Add background task to do the actual work
        background_tasks.add_task(
            process_rewordit_fix_task,
            text=text,
            user_id=user_id,
            user_name=user_name,
            response_url=response_url,
            db_session=db
        )
        
        # Return an immediate response (within 3 seconds) to Slack
        logger.info(f"Added paraphrase task to background for user {user_id}")
        return get_processing_layout()
        
    except Exception as e:
        logger.error(f"Error processing rephrase request for user {user_id}: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")

# Background task function for processing paraphrasing
async def process_paraphrase_task(
    text_to_rephrase: str,
    tone: str,
    user_id: str,
    user_name: str,
    response_url: str,
    db_session: Session
):
    try:
        # Get a new database session for this background task
        db = db_session
        slack_service = SlackService()
        # Process the rephrase request asynchronously
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(text_to_rephrase, tone)
        
        if not paraphrased_text:
            logger.error(f"Failed to get paraphrased text from service for user {user_id}")
            # Send error response
            await send_action_response(response_url, "error", slack_service)
            return
        
        # Store in the database
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id, user_name)
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=text_to_rephrase,
            paraphrased_text=paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        payload = {"response_url": response_url, "original_text": text_to_rephrase, "new_paraphrased_text": paraphrased_text, "user_id": user_id}
        await send_action_response(payload, "rephrased", slack_service)
        logger.info(f"Successfully processed paraphrase for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in background paraphrase task: {str(e)}", exc_info=True)
        # Send error to user
        payload = {"response_url": response_url, "error": str(e)}
        await send_action_response(payload, "error", slack_service)

# Background task function for processing rewrite action
async def process_rewrite_action_task(
    original_text: str,
    user_id: str,
    user_name: str,
    response_url: str,
    db_session: Session,
    tone: str | None = None
):
    try:
        # Get a new database session for this background task
        db = db_session
        slack_service = SlackService()
        # Get new paraphrased text
        paraphrase_service = ParaphraseService()
        new_paraphrased_text = await paraphrase_service.paraphrase(original_text, tone)
        
        if not new_paraphrased_text:
            logger.error(f"Failed to get paraphrased text for user {user_id}")
            # Send error response
            payload = {"response_url": response_url, "user_id": user_id}
            await send_action_response(payload, "error", slack_service)
            return
        
        # Store new paraphrase in database
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id, user_name)
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=original_text,
            paraphrased_text=new_paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        payload = {"response_url": response_url, "original_text": original_text, "new_paraphrased_text": new_paraphrased_text, "user_id": user_id}
        await send_action_response(payload, "rephrased", slack_service)
        logger.info(f"Successfully processed rewrite action for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error in background rewrite action task: {str(e)}", exc_info=True)
        # Send error to user
        payload = {"response_url": response_url, "error": str(e)}
        await send_action_response(payload, "error", slack_service)

async def process_rewordit_fix_task(
    text: str,
    user_id: str,
    user_name: str,
    response_url: str,
    db_session: Session
):
    try:
        # Get a new database session for this background task
        db = db_session
        slack_service = SlackService()
        
        # Process the rewordit fix request asynchronously
        paraphrase_service = ParaphraseService()
        fixed_text = await paraphrase_service.fix_text(text)
        
        if not fixed_text:
            logger.error(f"Failed to get fixed text for user {user_id}")
            # Send error response
            payload = {"response_url": response_url, "error": "Failed to get fixed text"}
            await send_action_response(payload, "error", slack_service)
    
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id, user_name)
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=text,
            paraphrased_text=fixed_text,
        )

        # Send the result to Slack
        payload = {"response_url": response_url, "original_text": text, "new_paraphrased_text": fixed_text, "user_id": user_id}
        await send_action_response(payload, "rephrased", slack_service)
        logger.info(f"Successfully processed rewordit fix for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in background rewordit fix task: {str(e)}", exc_info=True)
        # Send error to user
        payload = {"response_url": response_url, "error": str(e)}
        await send_action_response(payload, "error", slack_service)    

async def send_action_response(payload: dict, type: str, slack_service: SlackService):
    layout = get_action_response_layout(payload, type)
    await slack_service.send_action_response(payload["response_url"], layout)

def get_action_response_layout(payload: dict, type: str):
    if type == "acknowledgment":
        return get_acknowledgment_layout(payload["user_id"])  
    elif type == "error":
        return get_error_layout(payload["user_id"])
    elif type == "processing":
        return get_processing_layout()
    elif type == "rephrased":
        return get_rephrase_response_layout(payload["original_text"], payload["new_paraphrased_text"], payload["user_id"])
    else:
        raise ValueError(f"Invalid action response type: {type}")