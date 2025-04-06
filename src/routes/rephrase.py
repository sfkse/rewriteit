from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from src.models.slack import SlackPayload
from src.services.paraphrase import ParaphraseService
from src.services.database import DatabaseService
from src.database import get_db
from src.utils.text import parse_command
from src.utils.layout import get_layout, get_success_layout, get_modify_layout
from src.config import settings
import json
import logging
import httpx

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/rewrite")
async def rewrite(
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Received rewrite request with text: {text}")
        form_data = await request.form()
        logger.info(f"Request form data: {dict(form_data)}")

        # Get user ID from form data
        user_id = form_data.get("user_id")
        if not user_id:
            logger.error("No user_id found in form data")
            raise HTTPException(status_code=400, detail="Missing user_id")

        # Parse the command to get text and tone
        text_to_rephrase, tone = parse_command(text)
        logger.info(f"Parsed command - Text: {text_to_rephrase}, Tone: {tone}")

        # Get response_url for sending delayed responses
        response_url = form_data.get("response_url")
        if not response_url:
            logger.error("No response_url found in form data")
            raise HTTPException(status_code=400, detail="Missing response_url")

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
            logger.error("Failed to get paraphrased text from service")
            raise HTTPException(status_code=500, detail="Failed to paraphrase text")

        logger.info(f"Successfully paraphrased text. Original: {text_to_rephrase}, Paraphrased: {paraphrased_text}")

        # Store in the database with actual user ID
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)
        db_service.create_paraphrase(
            user_id=user.id,
            original_text=text_to_rephrase,
            paraphrased_text=paraphrased_text,
            tone=tone
        )
        logger.info(f"Successfully stored paraphrase in database for user {user_id}")

        # Send the delayed response to Slack with the paraphrased text
        await send_delayed_response(response_url, text_to_rephrase, paraphrased_text, user_id)

        return get_success_layout(text_to_rephrase, paraphrased_text, user_id)

    except Exception as e:
        logger.error(f"Error processing rephrase request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing request")


async def send_delayed_response(response_url: str, original_text: str, paraphrased_text: str, user_id: str):
    payload = get_layout(original_text, paraphrased_text, user_id)

    async with httpx.AsyncClient() as client:
        response = await client.post(response_url, json=payload)

    # Check if the response was successful
    if not response.is_success:
        logger.error(f"Failed to send delayed response to Slack. Status: {response.status_code}, Content: {response.text}")


@router.post("/rewrite-action")
async def rewrite_action(
    payload: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Parse the payload JSON string
        payload_data = json.loads(payload)
        logger.info(f"Received rewrite-action with payload: {payload_data}")

        # Get user ID and response URL
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
        logger.info("Sent acknowledgment response")

        # Get or create user and fetch their latest paraphrase
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(user_id)
        logger.info(f"User retrieved/created with ID: {user.id}")

        # Get the latest paraphrase for this user
        latest_paraphrases = db_service.get_user_paraphrases(user.id, limit=1)
        if not latest_paraphrases:
            logger.error("No previous paraphrases found for user")
            raise HTTPException(status_code=404, detail="No previous text to rephrase")

        latest_paraphrase = latest_paraphrases[0]
        original_text = latest_paraphrase.original_text
        paraphrased_text = latest_paraphrase.paraphrased_text

        if action_id == "rewrite_button":    
            # Get new paraphrased text
            paraphrase_service = ParaphraseService()
            new_paraphrased_text = await paraphrase_service.paraphrase(original_text)
            
            if not new_paraphrased_text:
                logger.error("Failed to get paraphrased text")
                raise HTTPException(status_code=500, detail="Failed to paraphrase text")

            logger.info(f"Successfully paraphrased text: {new_paraphrased_text}")
            
            # Store new paraphrase in database
            db_service.create_paraphrase(
                user_id=user.id,
                original_text=original_text,
                paraphrased_text=new_paraphrased_text,
                tone=None
            )
            logger.info("New paraphrase stored in database")
            
            # Send the delayed response to Slack with the paraphrased text
            await send_delayed_response(response_url, original_text, new_paraphrased_text, user_id)
            
            return {}

        elif action_id == "modify_button":
            # Return the modify layout with the current paraphrased text
            modify_layout = get_modify_layout(paraphrased_text, user_id)
            async with httpx.AsyncClient() as client:
                await client.post(response_url, json=modify_layout)
            return {}

        elif action_id == "cancel_modify_button":
            # Return to the original layout
            await send_delayed_response(response_url, original_text, paraphrased_text, user_id)
            return {}

        elif action_id == "send_modified_button":
            # Log the entire payload structure
            logger.info(f"Full payload for send_modified_button: {json.dumps(payload_data, indent=2)}")
            
            try:
                # Get the modified text from the input block
                block_id = "modify_input_block"
                action_id = "modified_text_input"
                modified_text = payload_data["state"]["values"][block_id][action_id]["value"]
                channel_id = payload_data["container"]["channel_id"]
                logger.info(f"Sending modified text to channel {channel_id}: {modified_text}")
                
                # Send the message to the channel
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {settings.slack_bot_token}",
                        "Content-Type": "application/json"
                    }
                    message_payload = {
                        "channel": channel_id,
                        "text": modified_text
                    }
                    response = await client.post(
                        f"{settings.slack_api_base_url}/chat.postMessage",
                        headers=headers,
                        json=message_payload
                    )
                    
                    if not response.is_success:
                        logger.error(f"Failed to send message to channel: {response.text}")
                        raise HTTPException(status_code=500, detail="Failed to send message to channel")
                    
                    # Send a confirmation message back to the user
                    success_payload = {
                        "response_type": "ephemeral",
                        "text": "Your message has been sent to the channel!"
                    }
                    await client.post(response_url, json=success_payload)
                    
                return {}
                
            except KeyError as e:
                logger.error(f"Failed to extract modified text from payload: {e}", exc_info=True)
                error_payload = {
                    "response_type": "ephemeral",
                    "text": "Sorry, there was an error processing your modified text. Please try again."
                }
                async with httpx.AsyncClient() as client:
                    await client.post(response_url, json=error_payload)
                return {}

    except Exception as e:
        logger.error(f"Error processing rephrase action: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing request") 
