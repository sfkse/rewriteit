import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.services.slack import SlackService
from src.utils.text import parse_command, get_latest_paraphrase
from src.utils.request import parse_request
from src.utils.layout import get_rephrase_response_layout, get_processing_layout, get_error_layout, get_acknowledgment_layout
from src.utils.auth import verify_slack_request, check_user_credits
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
        text, user_id, user_name, response_url = await parse_request(request)
        if not text:
            logger.error(f"No text found in form data for user {user_id}")
            return get_error_layout("Missing text")
        if not user_id:
            logger.error(f"No user_id found in form data for user {user_id}")
            return get_error_layout("Missing user_id")
        if not response_url:
            logger.error(f"No response_url found in form data for user {user_id}")
            return get_error_layout("Missing response_url")
        
        text_to_rephrase, tone = parse_command(text)     

        slack_service = SlackService()
        payload = get_acknowledgment_payload(user_id, response_url)
        await send_action_response(payload, "acknowledgment", slack_service, response_url)
        logger.info(f"Sent acknowledgment for user {user_id} for reword")
        
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
        logger.info(f"Added reword task to background for user {user_id}")
        return get_processing_layout()
        
    except Exception as e:
        logger.error(f"Error processing reword request for user {user_id}: {str(e)}", exc_info=True)
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
        form_data = await request.form()
        payload = form_data.get("payload")
        if not payload:
            logger.error("No payload found in form data")
            return get_error_layout("Missing payload")
            
        slack_service = SlackService()
        payload_data = json.loads(payload)
        user_id = payload_data["user"]["id"]
        user_name = payload_data["user"]["name"]
        response_url = payload_data["response_url"]
        action_id = payload_data["actions"][0]["action_id"]
    
        # Send immediate acknowledgment
        payload = get_acknowledgment_payload(user_id, response_url)
        await send_action_response(payload, "acknowledgment", slack_service, response_url)
        logger.info(f"Sent acknowledgment for user {user_id} for reword-action")
        
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
        logger.error(f"Error processing reword-action request for user {user_id}: {str(e)}", exc_info=True)
        return get_error_layout("Error processing request")

@router.post("/reword-fix")
async def reword_fix(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    is_verified: bool = Depends(verify_slack_request)
):
    if not is_verified:
        logger.error("Unauthorized request")
        return get_error_layout("Unauthorized")
    
    try:
        text, user_id, user_name, response_url = await parse_request(request)
        if not text:
            logger.error(f"No text found in form data for user {user_id}")
            return get_error_layout("Missing text")
        if not user_id:
            logger.error(f"No user_id found in form data for user {user_id}")
            return get_error_layout("Missing user_id")
        
        slack_service = SlackService()
        # Send acknowledgment via response_url (Slack will already have received this)
        payload = get_acknowledgment_payload(user_id, response_url)
        await send_action_response(payload, "acknowledgment", slack_service, response_url)
        logger.info(f"Sent acknowledgment for user {user_id} for reword-fix")
        
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
        logger.info(f"Added reword-fix task to background for user {user_id}")
        return get_processing_layout()
        
    except Exception as e:
        logger.error(f"Error processing reword-fix request for user {user_id}: {str(e)}", exc_info=True)
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
        slack_service = SlackService()
        db = db_session
        db_service = DatabaseService(db)

        user = db_service.get_or_create_user(user_id, user_name)
        has_credits = check_user_credits(user)
        if not has_credits:
            payload = get_error_payload("You have no credits left", text_to_rephrase, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        paraphrase_service = ParaphraseService()
        paraphrased_text = await paraphrase_service.paraphrase(text_to_rephrase, tone)
        
        if not paraphrased_text:
            logger.error(f"Failed to get rephrased text from service for user {user_id}")
            payload = get_error_payload("Failed to get rephrased text", text_to_rephrase, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=text_to_rephrase,
            paraphrased_text=paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        payload = get_rephrase_response_payload(text_to_rephrase, paraphrased_text, user_id)
        await send_action_response(payload, "rephrased", slack_service, response_url)
        logger.info(f"Successfully processed paraphrase for user {user_id}")

        # Update user credits
        db_service.update_user_credits(user.id)
    
    except Exception as e:
        logger.error(f"Error in background paraphrase task: {str(e)}", exc_info=True)
        payload = get_error_payload(str(e), text_to_rephrase, response_url)
        await send_action_response(payload, "error", slack_service, response_url)

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
        slack_service = SlackService()
        db = db_session
        db_service = DatabaseService(db)

        user = db_service.get_or_create_user(user_id, user_name)
        has_credits = check_user_credits(user)
        if not has_credits:
            payload = get_error_payload("You have no credits left", original_text, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        paraphrase_service = ParaphraseService()
        new_paraphrased_text = await paraphrase_service.paraphrase(original_text, tone)
        
        if not new_paraphrased_text:
            logger.error(f"Failed to get paraphrased text for user {user_id}")
            payload = get_error_payload("Failed to get paraphrased text", original_text, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=original_text,
            paraphrased_text=new_paraphrased_text,
            tone=tone
        )
        
        # Send the result to Slack
        payload = get_rephrase_response_payload(original_text, new_paraphrased_text, user_id)
        await send_action_response(payload, "rephrased", slack_service, response_url)
        logger.info(f"Successfully processed rewrite action for user {user_id}")

        # Update user credits
        db_service.update_user_credits(user.id)
    
    except Exception as e:
        logger.error(f"Error in background rewrite action task: {str(e)}", exc_info=True)
        payload = get_error_payload(str(e), original_text, response_url)
        await send_action_response(payload, "error", slack_service, response_url)

async def process_rewordit_fix_task(
    text: str,
    user_id: str,
    user_name: str,
    response_url: str,
    db_session: Session
):
    try:
        db = db_session
        slack_service = SlackService()               
        db_service = DatabaseService(db)
        
        user = db_service.get_or_create_user(user_id, user_name)
        has_credits = check_user_credits(user)
        if not has_credits:
            payload = get_error_payload("You have no credits left", text, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        paraphrase_service = ParaphraseService()
        fixed_text = await paraphrase_service.fix_text(text)
        
        if not fixed_text:
            logger.error(f"Failed to get fixed text for user {user_id}")
            payload = get_error_payload("Failed to get fixed text", text, response_url)
            await send_action_response(payload, "error", slack_service, response_url)
            return
        
        db_service.create_or_update_paraphrase(
            user_id=user.id,
            original_text=text,
            paraphrased_text=fixed_text,
        )

        # Send the result to Slack
        payload = get_rephrase_response_payload(text, fixed_text, user_id)
        await send_action_response(payload, "rephrased", slack_service, response_url)
        logger.info(f"Successfully processed rewordit fix for user {user_id}")

        # Update user credits
        db_service.update_user_credits(user.id)
        
    except Exception as e:
        logger.error(f"Error in background rewordit fix task: {str(e)}", exc_info=True)
        # Send error to user
        payload = get_error_payload(str(e), text, response_url)
        await send_action_response(payload, "error", slack_service, response_url)    

async def send_action_response(payload: dict, type: str, slack_service: SlackService, response_url: str):
    layout = get_action_response_layout(payload, type)
    await slack_service.send_action_response(response_url, layout)

def get_action_response_layout(payload: dict, type: str):
    if type == "acknowledgment":
        return get_acknowledgment_layout(payload["user_id"])  
    elif type == "error":
        return get_error_layout(payload["error"], payload["original_text"])
    elif type == "processing":
        return get_processing_layout()
    elif type == "rephrased":
        return get_rephrase_response_layout(payload["original_text"], payload["new_paraphrased_text"], payload["user_id"])
    else:
        raise ValueError(f"Invalid action response type: {type}")
    
def get_error_payload(error: str, original_text: str, response_url: str):
    return {"response_url": response_url, "error": error, "original_text": original_text}

def get_acknowledgment_payload(user_id: str, response_url: str):
    return {"response_url": response_url, "user_id": user_id}

def get_rephrase_response_payload(original_text: str, paraphrased_text: str, user_id: str):
    return {"original_text": original_text, "new_paraphrased_text": paraphrased_text, "user_id": user_id}