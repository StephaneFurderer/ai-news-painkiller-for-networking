from loguru import logger
from ..config.settings import settings
from ..core.models import ContentResponse

class MessageFormatter:
    """Format messages for different platforms with length constraints"""

    @staticmethod
    def format_for_telegram(content: str) -> ContentResponse:
        """Format content for Telegram with truncation if needed"""
        original_length = len(content)
        max_length = settings.max_message_length

        if original_length <= max_length:
            return ContentResponse(
                content=content,
                original_length=original_length,
                was_truncated=False,
                formatted_message=content
            )

        # Intelligently truncate at sentence or paragraph boundary
        truncated = content[:max_length]

        # Find best cut point
        last_sentence = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        cut_point = max(last_sentence, last_newline)

        if cut_point > max_length * 0.8:
            # Good cut point found
            formatted_message = content[:cut_point + 1] + "\n\n📝 [Full post truncated for Telegram]"
        else:
            # No good cut point, just truncate with ellipsis
            formatted_message = content[:max_length - 50] + "...\n\n📝 [Message truncated due to length]"

        logger.info(f"Message truncated from {original_length} to {len(formatted_message)} characters")

        return ContentResponse(
            content=content,
            original_length=original_length,
            was_truncated=True,
            formatted_message=formatted_message
        )

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters for Telegram"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text