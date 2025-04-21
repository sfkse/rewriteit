from fastapi import APIRouter, HTTPException
from starlette.responses import RedirectResponse
import httpx
import logging
from src.config import settings
from src.database import SessionLocal
from sqlalchemy.exc import IntegrityError
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signin-oidc")
async def slack_oauth(code: str):
    """Handle the OAuth callback from Slack"""
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            logger.info(f"Redirect URI: {settings.api_base_url}/signin-oidc")
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
            
            # Get user information from Slack
            user_info_response = await client.get(
                "https://slack.com/api/users.info",
                headers={"Authorization": f"Bearer {data['authed_user']['access_token']}"},
                params={"user": data['authed_user']['id']}
            )
            
            user_info = user_info_response.json()
            logger.info(f"User info: {user_info}")
            if not user_info.get("ok"):
                logger.error(f"Failed to get user info: {user_info.get('error')}")
                raise HTTPException(status_code=400, detail="Failed to get user information")
            
            # Create or update user in database
            db = SessionLocal()
            database_service = DatabaseService(db)

            try:
                user = database_service.get_or_create_user(data['authed_user']['id'], user_info['user']['name'])
                logger.info(f"User created: {user.slack_user_id}")
                # Redirect to success page
                return RedirectResponse(url=f"{settings.client_base_url}/success")
                
            except IntegrityError as e:
                db.rollback()
                logger.error(f"Database error: {str(e)}")
                raise HTTPException(status_code=500, detail="Database error occurred")
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error in Slack OAuth: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 