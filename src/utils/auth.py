from fastapi import Request
from src.config import settings
from src.models.database import User

import hmac
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

async def verify_slack_request(request: Request):
    request_body = await request.body()
    slack_signature = request.headers.get("X-Slack-Signature")
    slack_request_timestamp = request.headers.get("X-Slack-Request-Timestamp")
    
    # Check if the request is older than 5 minutes (to prevent replay attacks)
    if abs(time.time() - int(slack_request_timestamp)) > 60 * 5:
        logger.error("Request is older than 5 minutes")
        return False
    
    # Decode the request body to string
    request_body_str = request_body.decode('utf-8')
    
    # Compute the signature of the request body
    base_string = f"v0:{slack_request_timestamp}:{request_body_str}"
    computed_signature = f"v0={hmac.new(settings.slack_signing_secret.encode(), base_string.encode(), hashlib.sha256).hexdigest()}"
    
    # Compare the computed signature with the signature from the request headers
    return computed_signature == slack_signature

def check_user_credits(user: User):
    if not user:
        return False
    return user.credits_assigned > user.credits_used
