#!/usr/bin/env python3
"""
Manual Format Examples Loader
=============================

Simple script to manually add format examples to your Supabase database.
Just paste your examples here and run the script.
"""

import os
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def add_format_example(format_type: str, title: str, content: str, metadata: dict = None):
    """Add a format example to the database with embedding"""

    print(f"📝 Adding {format_type}: {title}")

    try:
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=content
        )
        embedding = response.data[0].embedding

        # Insert into database
        result = supabase.table('format_examples').insert({
            'format_type': format_type,
            'title': title,
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {}
        }).execute()

        print(f"✅ Added successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to add {title}: {e}")
        return False

def load_sample_examples():
    """Load a set of sample format examples"""

    print("🔄 Loading sample format examples...")

    # LinkedIn Post Examples
    add_format_example(
        format_type="linkedin_post",
        title="AI Breakthrough Announcement",
        content="""🚀 Exciting breakthrough in AI reasoning!

New research from Stanford shows remarkable improvements in:
• Complex reasoning tasks (+40% accuracy)
• Multi-step problem solving
• Mathematical proofs and logic

This could transform how we approach:
✓ Software development
✓ Scientific research
✓ Educational tools

The key insight? Teaching AI to "think step by step" dramatically improves performance.

What implications do you see for your industry?

#AI #Technology #Innovation #Research""",
        metadata={"tone": "professional", "length": "medium", "engagement": "high"}
    )

    add_format_example(
        format_type="linkedin_post",
        title="Productivity Tips",
        content="""💡 3 productivity hacks that changed my workflow:

1️⃣ Time-blocking: Schedule focused work in 2-hour chunks
   → No meetings, no slack, pure deep work

2️⃣ The 2-minute rule: If it takes <2 min, do it now
   → Prevents small tasks from becoming big problems

3️⃣ Weekly reviews: Every Friday, reflect and plan
   → What worked? What didn't? Adjust for next week

Small changes → massive impact on output quality.

Which productivity method works best for you? 👇

#Productivity #TimeManagement #WorkTips #Focus""",
        metadata={"tone": "helpful", "length": "short", "actionable": True}
    )

    # Twitter Thread Examples
    add_format_example(
        format_type="twitter_thread",
        title="Startup Lessons Thread",
        content="""🧵 5 hard lessons from building my first startup:

1/ Customer interviews > your brilliant idea
Talk to 100 potential customers before writing code. Your assumptions are probably wrong.

2/ MVP should be embarrassingly simple
If you're not slightly embarrassed by v1, you launched too late.

3/ Distribution is harder than building
Great product + no distribution = failed startup. Plan go-to-market from day 1.

4/ Cash flow > vanity metrics
Revenue matters more than downloads, users, or press coverage.

5/ Find a co-founder you'd want as a friend
You'll spend more time with them than family. Choose wisely.

What would you add to this list? 👇

#StartupLife #Entrepreneurship #Lessons""",
        metadata={"tone": "educational", "length": "long", "thread_length": 7}
    )

    add_format_example(
        format_type="twitter_thread",
        title="Remote Work Tips",
        content="""🏠 Remote work productivity secrets (learned the hard way):

1/ Create physical boundaries
Dedicated workspace = your brain knows it's "work time"

2/ Overcommunicate everything
What feels like too much communication is probably just right

3/ Schedule breaks like meetings
Put "walk" and "lunch" on your calendar or they won't happen

4/ End-of-day ritual
Close laptop, change clothes, or take a walk. Signal "work is done"

Remote work isn't just "work from home" - it's a completely different skill set.

What's your best remote work tip? 🤔""",
        metadata={"tone": "practical", "length": "medium", "thread_length": 6}
    )

    # Newsletter Examples
    add_format_example(
        format_type="newsletter",
        title="Weekly Tech Digest",
        content="""📰 This Week in Tech

👋 Hey there! Here's what caught my attention this week:

🔥 HOT TOPIC: Meta's New VR Breakthrough
Meta announced Quest 3 with mixed reality capabilities. The $499 price point makes VR accessible to mainstream consumers for the first time.

💡 WHY THIS MATTERS:
VR adoption has been slow due to cost and comfort issues. Quest 3 addresses both with:
• 40% lighter design
• 4K displays per eye
• Competitive pricing vs Apple Vision Pro

📊 BY THE NUMBERS:
• VR market expected to reach $87B by 2030
• 31% of US adults interested in VR for work
• Average session time increased to 45 minutes

🎯 ACTION ITEM FOR YOU:
If you're in product development, consider how VR/AR might enhance your user experience. Even simple 3D visualizations can differentiate your product.

📖 WEEKEND READ:
"The Metaverse Roadmap" by John Smart - essential reading for understanding where VR is heading beyond gaming.

That's all for this week. Stay curious!

-Alex

P.S. Hit reply and tell me what tech trends you're watching!""",
        metadata={"tone": "friendly", "length": "long", "sections": ["topic", "analysis", "data", "action", "recommendation"]}
    )

    # Blog Post Examples
    add_format_example(
        format_type="blog_post",
        title="How-To Guide Example",
        content="""# How to Build Your First RAG System in 30 Minutes

Building a Retrieval-Augmented Generation (RAG) system sounds complex, but it's surprisingly straightforward. Here's how to build one that actually works.

## What You'll Need
- Python 3.8+
- OpenAI API key
- 30 minutes of your time

## Step 1: Set Up Your Knowledge Base
The magic of RAG is giving your AI relevant context. Start simple:

```python
documents = [
    "Your company's FAQ",
    "Product documentation",
    "Best practices guide"
]
```

## Step 2: Create Embeddings
Convert your text into vectors that capture semantic meaning:

```python
from openai import OpenAI
client = OpenAI()

embeddings = []
for doc in documents:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc
    )
    embeddings.append(response.data[0].embedding)
```

## Step 3: Build the Retrieval
When a user asks a question, find the most relevant documents:

```python
def find_relevant_docs(query, top_k=3):
    # Convert query to embedding
    query_embedding = get_embedding(query)

    # Calculate similarities
    similarities = cosine_similarity(query_embedding, embeddings)

    # Return top matches
    return get_top_documents(similarities, top_k)
```

## Step 4: Generate with Context
Now the AI has relevant information to work with:

```python
def answer_question(query):
    relevant_docs = find_relevant_docs(query)

    prompt = f\"\"\"
    Context: {relevant_docs}
    Question: {query}
    Answer:
    \"\"\"

    return openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
```

## Why This Works
RAG combines the best of both worlds:
- **Retrieval**: Finds specific, factual information
- **Generation**: Creates natural, contextual responses

## Next Steps
1. Add more documents to your knowledge base
2. Experiment with different embedding models
3. Fine-tune your retrieval strategy
4. Add a simple web interface

That's it! You now have a working RAG system. The key is starting simple and iterating based on real usage.

*Have questions? Drop them in the comments below.*""",
        metadata={"tone": "instructional", "length": "long", "format": "tutorial", "code_included": True}
    )

    print(f"\n✅ Sample examples loaded! Check your Supabase dashboard.")

def add_your_examples():
    """Add your own format examples here"""

    print("\n📝 Add your own examples here:")
    print("Uncomment and modify the examples below:")

    # Uncomment and modify these examples:

    # add_format_example(
    #     format_type="your_format_type",
    #     title="Your Example Title",
    #     content="""Your example content here...""",
    #     metadata={"any": "metadata", "you": "want"}
    # )

def main():
    """Main function to load format examples"""

    print("🎯 Format Examples Loader")
    print("=" * 30)

    # Test connection
    try:
        result = supabase.table('format_examples').select('count').execute()
        current_count = len(result.data) if result.data else 0
        print(f"📊 Current format examples in database: {current_count}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # Load sample examples
    load_sample_examples()

    # Add your own examples
    add_your_examples()

    # Show final count
    try:
        result = supabase.table('format_examples').select('count').execute()
        final_count = len(result.data) if result.data else 0
        print(f"\n📊 Total format examples now: {final_count}")
    except Exception as e:
        print(f"❌ Could not get final count: {e}")

if __name__ == "__main__":
    main()