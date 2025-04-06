from pydantic import BaseModel
from typing import List, Optional

class OpenRouterMessage(BaseModel):
    role: str
    content: str

class OpenRouterChoice(BaseModel):
    message: OpenRouterMessage
    finish_reason: str

class OpenRouterResponse(BaseModel):
    id: str
    model: str
    choices: List[OpenRouterChoice]
    usage: dict 