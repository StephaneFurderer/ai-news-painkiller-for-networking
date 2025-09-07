# Personalized Discord News Bot

An AI Discord bot built with Modal (serverless platform) and Safron API (docs.safron.io) that provides personalized synthesized news reports for tech using social listening APIs and AI/LLM services.

The bot processes thousands of posts and comments from tech websites (Reddit, HN, Github, tech blogs, X, ArXiv) by preprocessing and caching data then through various prompt-chaining strategies produces an extensive report that should be interesting to a user based on their profile. 

Everything is citated back to exact sources so the user can vet the information.

![Discord Bot Example](example_discord.png)

**Note:** This is a first version, and a work in progress. 

## Tools used
1. **Modal**: for hosting, set with min_container=1 to prevent timeouts.
2. **Discord**: to run the bot through, setting up two commands (/setup and /news) user can run.
3. **Safron**: for structured data on the tech scene, using the keywords and ai-facts endpoints to gather data.
4. **MongoDB**: to store user profiles so it's easy for users to run /news without having to repeat themselves.
5. **LLMs**: Gemini and GPT is used to transform natural language into json inputs along with GPT-5 at the end that find themes and summarizes.

# How to setup

## Prerequisites

**Before setting up this bot, you'll need:**

- Python 3.13+
- A Discord application and bot setup via the Developer Portal
- Two Commands set up for the bot (/setup (required field about_me) & /news (optional field time_period)).
- Modal account
- MongoDB database
- API keys for AI services (Google & OpenAI)

### 2. Required Secrets

The bot requires the following environment variables to be set in Modal for a new secret called "safron-bot":

#### Discord Secrets
- `DISCORD_PUBLIC_KEY`: Your Discord application's public key (found in General Information)
- `BOT_TOKEN`: Your Discord bot token

#### Database
- `MONGO_DB_URI`: MongoDB connection string (e.g., `mongodb+srv://username:password@cluster.mongodb.net/`)

#### AI/LLM Services (Choose one or both)
- `GOOGLE_API_KEY`: Google Gemini API key
- `OPENAI_API_KEY`: OpenAI API key

![Secrets to set in Modal](secrets_modal.png)

## Deployment

Clone this repository:

```bash
git clone https://github.com/ilsilfverskiold/ai-personalized-tech-reports-discord.git
cd discord-bot
```

Setup your environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the requirements

```bash
pip install -r requirements.txt
```

Deploy the modal app

```bash
modal deploy app.py
```

You'll get an URL here you'll need to set as the webhook in Discord. Test the url and after this you should be good to do.

Make sure you have a MongoDB URI set too or the system won't be able to store the profile data via /setup. 

The cost of running the news report is two GPT-5 calls of around 1-2k tokens each for each run.


## Project Structure

```
discord-bot/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── helpers/
│   ├── commands/
│   │   ├── setup.py               # Setup command handler
│   │   └── news.py                # News command handler
│   ├── functions/
│   │   ├── api_utils.py           # API utilities
│   │   ├── discord_*.py           # Discord interaction handlers
│   │   ├── llm_*.py               # LLM integration
│   │   └── *.py                   # Various utility functions
│   └── config/
│       └── llm_schemas.py         # Pydantic schemas for LLM responses + system templates
```

## Dependencies

- **FastAPI**: Web framework for handling Discord interactions
- **Modal**: Serverless platform for deployment
- **Discord.py**: Discord API integration
- **MongoDB**: Database for storing user profiles
- **LlamaIndex**: LLM framework for AI processing
- **Google Generative AI**: Gemini API integration
- **OpenAI**: OpenAI API integration
- **PyNaCl**: Discord signature verification


## How It Works

The bot operates through two main commands that work together to deliver personalized news reports:

### 🔧 Setup Command (`/setup`)

**Purpose**: Create a personalized user profile for customized news delivery

1. **Profile Creation**: User provides their interests, work background, and keyword preferences
2. **AI Analysis**: LLM processes the input and categorizes keywords using Safron's category system
3. **Data Storage**: Profile is saved to MongoDB for future use
4. **Confirmation**: User receives confirmation that their profile is ready

### 📰 News Command (`/news`)

**Purpose**: Generate personalized news reports based on user profile

#### Step 1: Profile Retrieval
- Fetch user's saved profile from MongoDB
- If no profile exists, prompt user to run `/setup` first

#### Step 2: Keyword Discovery
- **Major categories**: Fetch top 3 trending keywords
- **Minor categories**: Fetch top 2 trending keywords  
- Use user's preferred time period (daily/weekly/monthly) or command override
- Include any custom keywords specified by the user

#### Step 3: Data Collection
- Use Safron's `ai-keyword-facts` endpoint to gather detailed information
- **Caching**: First-time keywords may be slow, subsequent calls are fast
- Collect posts, comments, and insights from various tech sources

#### Step 4: Data Processing
- Assemble and clean collected data
- Assign unique citation numbers for traceability
- Organize information by themes and relevance

#### Step 5: AI Summarization
- **Theme Analysis**: First LLM identifies key themes and corroborating facts
- **Report Generation**: Second LLM creates two versions:
  - **Concise**: Discord-friendly summary with key points
  - **Extended**: Detailed report accessible via web link
- Generate thread title and organize citations

#### Step 6: Delivery
- Post concise summary to Discord as a thread
- Include citation references and source links
- Provide access to extended report via web URL

## License

MIT
