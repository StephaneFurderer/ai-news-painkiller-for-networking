from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger
from ..core.models import ContentRequest
from ..handlers.content_handler import ContentHandler
from ..config.settings import settings

class TelegramHandler:
    """Handle Telegram bot interactions"""

    def __init__(self):
        self.content_handler = ContentHandler()
        self.app = None

    def create_application(self) -> Application:
        """Create and configure the Telegram application"""
        self.app = Application.builder().token(settings.telegram_bot_token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        return self.app

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        logger.info(f"Start command from user {user_id}")

        welcome_message = """
🤖 **Personal Content Writer Bot**

I help you create natural, human-like content that avoids typical AI patterns.

**How to use:**
1. Simply send me your content request
2. I'll generate authentic, engaging content
3. Content is automatically formatted for your platform

**Commands:**
/help - Show this help message

Ready to create some great content? Just send me your request!
        """

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
**Personal Content Writer Bot - Help**

**What I do:**
- Generate natural, human-like content
- Avoid AI-typical phrases and patterns
- Format content appropriately for different platforms

**Tips for better results:**
- Be specific about what you want
- Mention the target audience
- Include any style preferences
- Provide context when helpful

**Examples:**
• "Write a LinkedIn post about remote work benefits"
• "Create a casual email to my team about the new project"
• "Draft a blog intro about sustainable living"

Need more help? Just ask!
        """

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages from users"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        user_text = update.message.text

        logger.info(f"Message from user {user_id} (@{username}): {user_text[:100]}...")

        # Create content request
        request = ContentRequest(
            user_input=user_text,
            user_id=user_id,
            context={"username": username}
        )

        # Process the request
        result = await self.content_handler.process_request(request)

        if result.success:
            # Send the generated content
            formatted_message = result.data["formatted_message"]
            await update.message.reply_text(formatted_message)

            # Optionally send info about truncation
            if result.data.get("was_truncated"):
                info_message = f"ℹ️ Original content was {result.data['original_length']} characters, truncated for Telegram."
                await update.message.reply_text(info_message)

        else:
            # Send error message
            await update.message.reply_text(result.message)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

    def run(self):
        """Run the bot"""
        if not self.app:
            self.create_application()

        # Add error handler
        self.app.add_error_handler(self.error_handler)

        logger.info("Starting Telegram bot...")
        self.app.run_polling()