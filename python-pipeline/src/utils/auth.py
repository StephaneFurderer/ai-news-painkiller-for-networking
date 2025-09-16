from loguru import logger
from ..config.settings import settings

class AuthManager:
    """Handle user authentication and authorization"""

    @staticmethod
    def is_authorized_user(user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        authorized = user_id == settings.authorized_user_id

        if not authorized:
            logger.warning(f"Unauthorized access attempt from user ID: {user_id}")
        else:
            logger.info(f"Authorized user {user_id} accessing bot")

        return authorized

    @staticmethod
    def get_unauthorized_message() -> str:
        """Return message for unauthorized users"""
        return "⚠️ You are not authorized to use this bot."