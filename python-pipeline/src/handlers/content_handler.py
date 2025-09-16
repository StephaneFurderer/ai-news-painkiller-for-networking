from loguru import logger
from typing import Dict, Any
from ..core.openai_client import OpenAIClient
from ..core.models import ContentRequest, ProcessingResult
from ..utils.message_formatter import MessageFormatter
from ..utils.auth import AuthManager

class ContentHandler:
    """Handle content generation requests with validation and formatting"""

    def __init__(self):
        self.openai_client = OpenAIClient()
        self.formatter = MessageFormatter()
        self.auth_manager = AuthManager()

    async def process_request(self, request: ContentRequest) -> ProcessingResult:
        """Process a content generation request"""
        try:
            # Check authorization
            if not self.auth_manager.is_authorized_user(request.user_id):
                return ProcessingResult(
                    success=False,
                    message=self.auth_manager.get_unauthorized_message()
                )

            # Validate input
            is_valid = await self.openai_client.validate_input(request.user_input)
            if not is_valid:
                logger.warning(f"Invalid input from user {request.user_id}: {request.user_input[:100]}...")
                return ProcessingResult(
                    success=False,
                    message="❌ Your input doesn't appear to be a valid content request. Please try again."
                )

            # Generate content
            context = request.context.get("additional_context", "") if request.context else ""
            content = await self.openai_client.generate_content(request.user_input, context)

            # Format for platform
            formatted_response = self.formatter.format_for_telegram(content)

            logger.info(f"Successfully processed request for user {request.user_id}")

            return ProcessingResult(
                success=True,
                message="✅ Content generated successfully",
                data={
                    "formatted_message": formatted_response.formatted_message,
                    "original_length": formatted_response.original_length,
                    "was_truncated": formatted_response.was_truncated
                }
            )

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return ProcessingResult(
                success=False,
                message="❌ An error occurred while processing your request. Please try again."
            )