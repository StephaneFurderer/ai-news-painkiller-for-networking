# AI Content Generation Pipeline

A Python implementation of the n8n personal writer workflow, structured using patterns from the ai-resources folder.

## Features

- **Content Generation**: Natural, human-like content using OpenAI GPT
- **Telegram Integration**: Bot interface for easy interaction
- **Smart Formatting**: Automatic message truncation and formatting for Telegram
- **User Authentication**: Authorized user access control
- **Input Validation**: Content request validation before processing
- **Structured Architecture**: Clean separation of concerns inspired by ai-resources patterns

## Project Structure

```
python-pipeline/
├── src/
│   ├── config/           # Configuration and prompts
│   │   ├── settings.py   # Environment settings
│   │   └── prompts.py    # AI prompts
│   ├── core/             # Core functionality
│   │   ├── models.py     # Pydantic models
│   │   └── openai_client.py  # OpenAI API client
│   ├── handlers/         # Request handlers
│   │   ├── content_handler.py    # Content processing logic
│   │   └── telegram_handler.py   # Telegram bot handling
│   └── utils/            # Utility functions
│       ├── auth.py       # Authentication utilities
│       └── message_formatter.py  # Message formatting
├── tests/                # Test files
├── logs/                 # Log files
├── main.py              # Main entry point
├── requirements.txt     # Dependencies
└── .env.example        # Environment template
```

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd ai-news-painkiller-for-networking/python-pipeline
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Required environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `AUTHORIZED_USER_ID`: Your Telegram user ID
   - `MAX_MESSAGE_LENGTH`: Maximum message length (default: 4000)

## Usage

1. **Run the bot:**
   ```bash
   python main.py
   ```

2. **Interact with the bot on Telegram:**
   - Send `/start` to begin
   - Send `/help` for assistance
   - Send any text to generate content

## Architecture Patterns

This implementation uses several patterns inspired by the ai-resources folder:

### 1. **Prompt Chaining**
- Input validation → Content generation → Formatting

### 2. **Structured Output**
- Pydantic models for type safety and validation
- Clear data flow between components

### 3. **Modular Design**
- Separate handlers for different concerns
- Reusable utility functions
- Clean configuration management

### 4. **Error Handling**
- Comprehensive logging with loguru
- Graceful error recovery
- User-friendly error messages

## Extending the Pipeline

To add new functionality:

1. **Add new models** in `src/core/models.py`
2. **Create new handlers** in `src/handlers/`
3. **Add utility functions** in `src/utils/`
4. **Update configuration** in `src/config/`

## Learning Objectives

This project demonstrates:

- **Clean Python architecture** for AI applications
- **Integration patterns** for external APIs (OpenAI, Telegram)
- **Content processing** and formatting
- **Authentication and validation** patterns
- **Error handling** and logging best practices