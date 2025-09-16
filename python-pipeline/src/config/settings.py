from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    telegram_bot_token: str
    authorized_user_id: int
    max_message_length: int = 4000
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()