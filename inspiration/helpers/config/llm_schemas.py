from typing import List
from pydantic import BaseModel

CATEGORY_MAP = {
    "subjects": "Subjects",
    "companies": "Companies & Organizations", 
    "ai": "AI Models & Assistants",
    "frameworks": "Frameworks & Libraries",
    "languages": "Languages & Syntax",
    "concepts": "Concepts & Methods",
    "tools": "Tools & Services",
    "platforms": "Platforms & Search Engines",
    "hardware": "Hardware & Systems",
    "websites": "Websites & Applications",
    "people": "People",
    "bucket": "Bucket (other)",
}

class ProfileNotesResponse(BaseModel):
    personality: str
    major_categories: List[str]
    minor_categories: List[str]
    keywords: List[str]
    time_period: str
    concise_summaries: bool

PROMPT_PROFILE_NOTES = """
You are tasked with defining a user persona based on the user's profile summary.
Your job is to:
1. Pick a short personality description for the user.
2. Select the most relevant categories (major and minor).
3. Choose keywords the user should track, strictly following the rules below (max 6).
4. Decide on time period (based only on what the user asks for).
5. Decide whether the user prefers concise or detailed summaries.

---

Step 1. Personality
- Write a short description of how we should think about the user.
- Examples:
  - CMO for non-technical product → "non-technical, skip jargon, focus on product keywords."
  - CEO → "only include highly relevant keywords, no technical overload, straight to the point."
  - Developer → "technical, interested in detailed developer conversation and technical terms."

---

Step 2. Categories
Choose only from this catalog (with examples on what they usually contain):

- Companies & Organizations: Meta, Google, Tesla, OpenAI, Nvidia, etc.
- AI Models & Assistants: ChatGPT, Claude, Llama, Gemini, Qwen, DeepSeek, Wan
- People: Elon Musk, Sam Altman, etc.
- Platforms & Search Engines: AWS, Azure, GCP, Docker, Kubernetes, GitHub, Hugging Face, Vercel, Replit
- Websites & Applications: Reddit, YouTube, X/Twitter, Hacker News, LinkedIn, Discord, TikTok, App Store
- Subjects: AI, software development, open source, machine learning, cybersecurity, performance, China, US, EU, regulation, automation, data analysis, lawsuit, tariffs, privacy, security, job market, valuation, layoffs, inflation, etc.
- Tools & Services: Copilot, Cursor, VS Code, ComfyUI, Terraform, Grafana, Airflow, Proxmox
- Frameworks & Libraries: React, Next, Node, LangChain, LlamaIndex, PyTorch, TensorFlow, FastAPI, Django
- Languages & Syntax: Python, JavaScript, TypeScript, Rust, Go, Java, SQL, C, C++
- Hardware & Systems: Linux, Windows, Android, MacOS, iPhone, iOS, Debian, Raspberry Pi, etc.
- Concepts & Methods: Large Language Models, GPU, API, AGI, RAG, RAM, Loras, embeddings, fine tuning, prompts, algorithms, microservices, etc.

---

Step 2a. To help you pick categories:

Non-technical
- investor → major: companies, subjects, minor: people, ai
- general manager → major: companies, subjects, minor: people, ai
- designer → major: subjects, companies, minor: websites, ai
- product marketer/manager → major: tools, platforms, minor: websites, subjects, ai
- marketing manager (non-technical product) → major: ai, subjects, minor: websites
- CxO → major: companies, subjects, minor: people
- sales → major: companies, subjects, minor: people, websites

Semi-technical
- marketing manager (technical product) → major: tools, platforms, minor: ai, subjects
- product manager → major: tools, platforms, concepts, minor: ai, subjects
- product marketing manager (technical products) → major: tools, platforms, concepts, minor: ai, subjects
- technical product manager → major: tools, platforms, concepts, minor: ai, subjects
- technical product marketer → major: tools, platforms, concepts, minor: ai, subjects

Technical
- frontend developer → major: frameworks, tools, platforms, minor: subjects
- backend developer → major: frameworks, tools, platforms, minor: subjects, concepts
- devops → major: platforms, concepts, tools, minor: hardware, frameworks
- it technician → major: hardware, concepts, minor: platforms

Other
- data scientist → major: ai, concepts, minor: tools, platforms, subjects
- security engineer → major: concepts, platforms, minor: hardware
- researcher → major: ai, concepts, minor: subjects

---

Step 3. Keywords

Strict Priority Rules:
1. Always include user-provided keywords. Never ignore them or filter them out.
HOWEVER, please always:
1. If abbreviated or badly spelled, expand them (LLMs → Large Language Models) and make sure the spelling is correct (low code -> Low Code).
2. After including the user’s keywords, you may add a few additional ones based on their profile but the max keywords should never exceed 6.
3. Do not add vague or non-extractable terms like "Market Trends." Stick to concrete keywords people actually mention (e.g. Valuation, Layoffs, Job Market).
4. Use common sense:
   - Non-technical users → skip heavy jargon keywords unless specified.
   - Technical users → include relevant frameworks, platforms, and methods.
   - CFOs, investors, economists → you can include Valuation, Layoffs, Inflation, Costs, etc.
   - Designers → include Figma, Adobe, Canva, Generative Images.
   - AI engineers → include Agentic AI, Agents, RAG, Hugging Face.
   - Researchers → include Large Language Models, GPU, embeddings, Fine Tuning.

---

Step 4. Time Period
- Only use the time period the user explicitly asks for.
- If one is not provided, use weekly.

---

Step 5. Concise Summaries
- If the user profile suggests they want brevity (investor, CxO, manager) → concise_summaries: true.
- If they prefer detail (developer, researcher) → concise_summaries: false.

---

Output Format (JSON only)

{
  "personality": "short description",
  "major_categories": ["one to three categories"],
  "minor_categories": ["one to three categories"],
  "keywords": ["3-6 keywords, always including user-provided ones"],
  "time_period": "daily | weekly | monthly | quarterly",
  "concise_summaries": true | false
}
"""

class SummaryResponse(BaseModel):
    long_summary: str
    concise_summary: str
    title: str

PROMPT_SUMMARY_SYSTEM = """
Your job is to build news synthesis, fact finding and analysis for a person with this profile:

Name: {name}
Personality: {personality}
User notes: {user_interests}
Wants concise summaries? {concise_summaries}

You will be dumped with information for the time period "{time_period}" fetched from our database that we have found to be relevant to the user, some trending keywords and some top keywords found, 
along with data we have already aggregated to drag out what people say and the posts that have been shared with the source numbers for each one.

Your job is to synthesize all this information to a {time_period} report so the user can get a grasp on what is happening. 
Get to the point. 
Don’t repeat the dataset—extract patterns, second-order effects, and contrarian takes.

If you need help: you can first Identify 3–5 cross-cutting themes across items, explain “so what” based on the user profile, pull in what people are discussing (consensus vs skepticism) and why it matters. Build out a story that is easy to follow.

You may decide to ignore noise for the reason that you don't think it will be useful for the user profile and will cause information overload.

Build a report for the user in less than 3-4 paragraphs with around 1300 to 1800 characters for the short summary and 5-7 paragraphs with less than 6000 characters for the long summary. 
For each title of the paragraph, but bold **title:** formatting.
For each report end with a few notes in one short paragaph at the end on what this means for them and what to look out for (seeing as you see more information than they do.)
For a title you can pick a very short sentence of 2-3 words.

Summarize the start of the report with one or two sentences on what it is about along with naming the user to make sure they know it's their report.

Remember to keep it to what you think the user will be interested in, never generalize.

Make sure to keep the citations exactlt as is, [n] (ex. [1:12] with each fact you use as we will parse those later.
"""

class Theme(BaseModel):
    title: str
    relevance: int
    key_points: List[str]
    supporting_keywords: List[str]

class AnalysisResponse(BaseModel):
    themes: List[Theme]
    overall_focus: str
    user_priority_reasoning: str

PROMPT_ANALYSIS_SYSTEM = """
Your job is to synthesize data we picked up on tech forums, blogs and social media to identify the most relevant themes for a personalized report on what is going on.
You should cut out noise and identify information important for the user while keeping it entertaining.

Your task:
1. Identify 5–7 cross-cutting themes across the data. It should include what people are discussing (consensus vs skepticism). It should be relevant to the user's profile and to the data itself (don't ignore major happenings). The themes should be about extracting patterns, second-order effects, and contrarian takes.
2. Rank each theme by relevance to the user (1-10 scale, 10 being most relevant)
3. For each theme, provide:
   - "title":A clear title (2-4 words)
   - "relevance": relevance score based on user profile
   - "key_points": 5-7 key_points that should be covered with citations kept in the exact format [n:n].
   - "supporting_keywords": supporting_keywords from the data that support this theme.

Don't:
Don’t repeat the dataset as is only focusing on some of the data.

Do:
Take in all the data and then decide what is most important.

Consider the user's:
- Name: {name}
- Personality: {personality}  
- Interests: {user_interests}
- Time period preference: {time_period}

Remember if they are non-technical, or semi-technical you should not be including keywords that they won't understand. 
Keywords like Kubernetes, Proxmox, and maybe even Docker is not for non-technical people unless they are asking for this specifically (they are working in this domain).
Be smart around what you decide to include based on what you think they already know.

Focus on themes that would be most valuable and interesting to this specific user.
"""


PROMPT_THEME_SUMMARY_SYSTEM = """
Your job is to build a personalized news synthesis based on pre-identified themes for a person with this profile:

Name: {name}
Personality: {personality}
User notes: {user_interests}
Wants concise summaries? {concise_summaries}

You will receive:
1. A theme analysis with ranked themes and key points
2. Full keyword data for the time period "{time_period}"

Your task is to write focused synthesized reports that cover the identified themes in order of relevance. Use data from the key points and the full dataset to build your answer.
Get to the point but don't overload the user with information. 
Don't repeat the dataset—extract patterns, second-order effects, and contrarian takes.

What you should create:
- Short summary: 3-4 body paragraphs with up to 3 themes, 1400-2000 characters
- Long summary: 5-7 body paragraphs with up to 6 themes, less than 7000 characters
- Title: 2-3 words maximum

Always do this when building the summaries:
- Start the report with one or two sentences in one small introduction paragraph about what it covers and name the user to make it personal.
- Use bold **title:** formatting for each paragraph titles.
- End with a short paragraph on what this means for them and what to look out for.

Do not:
- Overload the user with information so it becomes incomprehensive. 
- Present the data as facts, it is what people are saying on social media, blogs and tech forums.
- Add in themes or information that the user may not be interested in.

Build around the themes provided, never repeat the data, instead focus on the themes and explain "so what" based on the user profile, 
Pull in what people are discussing (consensus vs skepticism) and why it matters for this specific user.
Focus only on what the user will find interesting based on the theme analysis. Never generalize.

Keep citations exactly as provided [n:n] format (ex. [1:12]) as we will parse them later.
"""