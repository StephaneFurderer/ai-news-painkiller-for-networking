from pydantic import BaseModel
from typing import Optional, Dict, Any

class TelegramMessage(BaseModel):
    message_id: int
    from_user_id: int
    username: Optional[str]
    text: str
    chat_id: int

class ContentRequest(BaseModel):
    user_input: str
    user_id: int
    context: Optional[Dict[str, Any]] = None

class ContentResponse(BaseModel):
    content: str
    original_length: int
    was_truncated: bool
    formatted_message: str

class ProcessingResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None