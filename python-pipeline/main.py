#!/usr/bin/env python3
"""
AI Content Generation Pipeline - Main Entry Point

This application replicates the n8n personal writer pipeline in Python,
structured using patterns from the ai-resources folder.
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from src.handlers.telegram_handler import TelegramHandler

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure logging"""
    logger.add(
        "logs/bot.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )

def main():
    """Main entry point"""
    logger.info("Starting AI Content Generation Pipeline")

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    setup_logging()

    # Create and run telegram handler
    telegram_handler = TelegramHandler()

    try:
        telegram_handler.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise

if __name__ == "__main__":
    main()