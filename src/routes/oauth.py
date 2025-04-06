from fastapi import APIRouter, HTTPException
import httpx
import logging
from src.config import settings
from src.models import SlackOAuthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signin-oidc")
async def slack_oauth(code: str):
    """Handle the OAuth callback from Slack"""
    logger.info(f"Received code: {code[:10]}...")  # Log only first 10 chars for security
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Using data parameter with headers for x-www-form-urlencoded
            response = await client.post(
                settings.slack_api_base_url + "/oauth.v2.access",
                headers=headers,
                data={
                    "code": code,
                    "client_id": settings.slack_client_id,
                    "client_secret": settings.slack_client_secret,
                    "redirect_uri": settings.api_base_url + "/signin-oidc",
                }
            )
            
            data = response.json()
            logger.info(f"Slack API response status: {response.status_code}")
            logger.info(f"Slack API response: {data}")
            
            if not response.is_success or not data.get("ok"):
                error_msg = data.get("error", "Failed to exchange code for token")
                logger.error(f"Slack API error: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )
            
            return SlackOAuthResponse(
                ok=True,
                access_token=data.get("access_token"),
                bot_token=data.get("access_token")
            )
        except Exception as e:
            logger.error(f"Error during Slack OAuth: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during OAuth: {str(e)}"
            ) 