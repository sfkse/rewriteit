from pydantic import BaseModel
from typing import Optional

class SlackOAuthResponse(BaseModel):
    ok: bool
    access_token: str
    bot_token: str | None = None
    error: Optional[str] = None 

class SlackPayload(BaseModel):
    token: str
    team_id: str
    team_domain: str
    channel_id: str
    channel_name: str
    user_id: str