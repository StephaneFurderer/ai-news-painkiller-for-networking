#!/usr/bin/env python3
"""
PostgreSQL Vector Database + RAG Tutorial Sandbox
=================================================

This is your hands-on learning sandbox for:
1. PostgreSQL with pgvector extension for vector storage
2. Text embeddings and similarity search
3. RAG (Retrieval-Augmented Generation) concepts

What you'll learn:
- How vectors represent text semantically
- How to store and query vectors in PostgreSQL
- How to build a simple RAG system
- Best practices for chunking and retrieval

Prerequisites:
- PostgreSQL with pgvector extension installed
- pip install psycopg2-binary openai numpy

To install pgvector locally:
1. Install PostgreSQL
2. Install pgvector extension: https://github.com/pgvector/pgvector#installation
"""

import psycopg2
import psycopg2.extras
import json
import numpy as np
from openai import OpenAI
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class VectorDBSandbox:
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize connection to PostgreSQL with pgvector

        db_config should contain: host, database, user, password, port
        """
        self.db_config = db_config
        self.conn = None
        self.connect()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ Connected to PostgreSQL")

            # Enable pgvector extension
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.conn.commit()
                print("✅ pgvector extension enabled")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("💡 Make sure PostgreSQL is running and pgvector is installed")

    def setup_tables(self):
        """
        Create tables for our RAG system

        Key concepts:
        - We store text chunks with their vector embeddings
        - Vector similarity search finds semantically similar content
        - Metadata helps us organize and filter results
        """

        with self.conn.cursor() as cur:
            # Drop existing table for clean start
            cur.execute("DROP TABLE IF EXISTS format_examples;")

            # Create table with vector column
            # vector(1536) = OpenAI embedding dimension
            cur.execute("""
                CREATE TABLE format_examples (
                    id SERIAL PRIMARY KEY,
                    format_type VARCHAR(100) NOT NULL,
                    example_title VARCHAR(200),
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create index for fast vector similarity search
            # This is crucial for performance!
            cur.execute("""
                CREATE INDEX ON format_examples
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)

            self.conn.commit()
            print("✅ Tables created with vector index")

    def get_embedding(self, text: str) -> List[float]:
        """
        Convert text to vector embedding using OpenAI

        Concept: Embeddings capture semantic meaning
        Similar texts have similar vectors (high cosine similarity)
        """
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",  # Latest OpenAI embedding model
                input=text
            )
            embedding = response.data[0].embedding
            print(f"📊 Generated embedding for text: '{text[:50]}...' (dimension: {len(embedding)})")
            return embedding

        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return []

    def add_example(self, format_type: str, title: str, content: str, metadata: Dict = None):
        """
        Add a format example to our vector database

        Process:
        1. Generate embedding for the content
        2. Store text + embedding + metadata in PostgreSQL
        """

        # Generate embedding
        embedding = self.get_embedding(content)
        if not embedding:
            return False

        # Store in database
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO format_examples (format_type, example_title, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (format_type, title, content, embedding, json.dumps(metadata or {})))

            self.conn.commit()
            print(f"✅ Added example: {title} ({format_type})")
            return True

    def search_similar_examples(self, query_text: str, format_type: str = None, limit: int = 3) -> List[Dict]:
        """
        RAG CORE: Find examples similar to query text

        How it works:
        1. Convert query to embedding
        2. Use cosine similarity to find closest vectors
        3. Return most relevant examples

        This is the "Retrieval" part of RAG!
        """

        # Get query embedding
        query_embedding = self.get_embedding(query_text)
        if not query_embedding:
            return []

        # Build SQL query with vector similarity
        sql = """
            SELECT
                format_type,
                example_title,
                content,
                metadata,
                1 - (embedding <=> %s::vector) as similarity_score
            FROM format_examples
        """
        params = [query_embedding]

        # Filter by format if specified
        if format_type:
            sql += " WHERE format_type = %s"
            params.append(format_type)

        # Order by similarity (closest first) and limit results
        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, limit])

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            results = cur.fetchall()

        # Convert to readable format
        examples = []
        for row in results:
            # Handle metadata - could be dict (JSONB) or string (JSON)
            metadata = row[3]
            if isinstance(metadata, str):
                metadata = json.loads(metadata) if metadata else {}
            elif metadata is None:
                metadata = {}

            examples.append({
                'format_type': row[0],
                'title': row[1],
                'content': row[2],
                'metadata': metadata,
                'similarity_score': float(row[4])
            })

        print(f"🔍 Found {len(examples)} similar examples for: '{query_text[:50]}...'")
        for ex in examples:
            print(f"   📄 {ex['title']} (similarity: {ex['similarity_score']:.3f})")

        return examples

    def demonstrate_rag_pipeline(self, user_content: str, target_format: str):
        """
        Full RAG demonstration: Retrieve relevant examples, then generate content

        This shows how you'd integrate RAG into your existing pipeline
        """

        print(f"\n🎯 RAG Demo: Writing {target_format} for content about: '{user_content[:100]}...'")
        print("="*80)

        # Step 1: RETRIEVE similar examples
        print("1️⃣ RETRIEVAL: Finding similar format examples...")
        similar_examples = self.search_similar_examples(
            query_text=user_content,
            format_type=target_format,
            limit=2
        )

        if not similar_examples:
            print("❌ No examples found!")
            return

        # Step 2: AUGMENT prompt with retrieved examples
        print("\n2️⃣ AUGMENTATION: Building context with examples...")
        examples_context = ""
        for i, example in enumerate(similar_examples, 1):
            examples_context += f"\nExample {i} ({example['similarity_score']:.3f} similarity):\n"
            examples_context += f"Title: {example['title']}\n"
            examples_context += f"Content: {example['content']}\n"
            examples_context += "-" * 40

        # Step 3: GENERATE with augmented context
        print("\n3️⃣ GENERATION: Creating content using examples as inspiration...")

        prompt = f"""
        Write a {target_format} based on this content: {user_content}

        Use these examples as inspiration for style and structure:
        {examples_context}

        Make it engaging and follow the format conventions shown in the examples.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert at writing {target_format} content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            generated_content = response.choices[0].message.content
            print(f"\n✨ GENERATED {target_format.upper()}:")
            print("="*50)
            print(generated_content)
            print("="*50)

            return generated_content

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return None

def main():
    """
    Interactive tutorial - learn by doing!
    """

    print("🎓 PostgreSQL Vector Database + RAG Tutorial")
    print("=" * 50)

    # Database configuration
    # Update these for your local PostgreSQL setup
    db_config = {
        'host': 'localhost',
        'database': 'vector_sandbox',  # Create this database first
        'user': 'sf',       # Your PostgreSQL user
        'password': '',   # Your PostgreSQL password
        'port': 5432
    }

    print("📝 Update db_config above with your PostgreSQL credentials")
    print("💡 Create database: CREATE DATABASE vector_sandbox;")
    print("\nPress Enter when ready to continue...")
    input()

    # Initialize sandbox
    try:
        sandbox = VectorDBSandbox(db_config)
        sandbox.setup_tables()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct")
        return

    # Add sample format examples
    print("\n📚 Adding sample format examples...")

    # LinkedIn post examples
    sandbox.add_example(
        format_type="linkedin_post",
        title="AI Breakthrough Announcement",
        content="""🚀 Exciting breakthrough in AI reasoning!

Scientists at OpenAI just released GPT-4, showing remarkable improvements in:
• Complex reasoning tasks (+40% accuracy)
• Code generation and debugging
• Mathematical problem solving

This could transform how we approach software development and research.

What are your thoughts on AI's rapid progress?

#AI #Technology #Innovation #GPT4""",
        metadata={"industry": "tech", "tone": "professional", "length": "medium"}
    )

    sandbox.add_example(
        format_type="linkedin_post",
        title="Productivity Tips",
        content="""💡 3 productivity hacks that changed my workflow:

1️⃣ Time-blocking: Schedule focused work in 2-hour chunks
2️⃣ The 2-minute rule: If it takes <2 min, do it now
3️⃣ Weekly reviews: Reflect and plan every Friday

Small changes, massive impact on output quality.

Which productivity method works best for you?

#Productivity #TimeManagement #WorkTips""",
        metadata={"industry": "general", "tone": "helpful", "length": "short"}
    )

    # Twitter thread examples
    sandbox.add_example(
        format_type="twitter_thread",
        title="Startup Lessons Thread",
        content="""🧵 5 hard lessons from building my first startup:

1/ Customer interviews > your brilliant idea
Talk to 100 potential customers before writing a single line of code. Your assumptions are probably wrong.

2/ MVP should be embarrassingly simple
If you're not slightly embarrassed by your first version, you launched too late.

3/ Distribution is harder than building
Great product + no distribution = failed startup. Plan your go-to-market from day 1.

4/ Cash flow > vanity metrics
Revenue matters more than downloads, users, or press coverage.

5/ Find a co-founder you'd want as a friend
You'll spend more time with them than your family. Choose wisely.

What would you add to this list? 👇""",
        metadata={"industry": "startup", "tone": "educational", "length": "long"}
    )

    # Newsletter examples
    sandbox.add_example(
        format_type="newsletter",
        title="Weekly Tech Digest",
        content="""📰 This Week in Tech

👋 Hey there! Here's what caught my attention this week:

🔥 HOT TOPIC: Meta's new VR headset
Meta announced Quest 3 with mixed reality capabilities. Price point at $499 makes VR accessible to mainstream consumers for the first time.

💡 INSIGHT: Why this matters
VR adoption has been slow due to cost and comfort. Quest 3 addresses both issues with lighter design and competitive pricing.

📊 BY THE NUMBERS:
• VR market expected to reach $87B by 2030
• 31% of US adults interested in VR for work
• Average VR session time: 25 minutes

🎯 ACTION ITEM:
If you're in product development, consider how VR/AR might enhance your user experience. Even simple 3D visualizations can differentiate your product.

📖 WEEKEND READ:
"The Metaverse Roadmap" - essential reading for understanding where VR is heading.

Stay curious!
-Alex""",
        metadata={"industry": "tech", "tone": "friendly", "length": "long"}
    )

    print("✅ Sample examples added!")

    # Interactive demonstrations
    print("\n🎮 Let's try some RAG queries!")

    # Demo 1: Search by content similarity
    print("\n" + "="*60)
    print("DEMO 1: Content Similarity Search")
    print("="*60)

    query = "artificial intelligence breakthrough in reasoning capabilities"
    print(f"Query: '{query}'")
    results = sandbox.search_similar_examples(query, limit=2)

    # Demo 2: Format-specific search
    print("\n" + "="*60)
    print("DEMO 2: Format-Specific Search")
    print("="*60)

    query = "startup advice and entrepreneurship tips"
    print(f"Query: '{query}' (Twitter threads only)")
    results = sandbox.search_similar_examples(query, format_type="twitter_thread", limit=2)

    # Demo 3: Full RAG pipeline
    print("\n" + "="*60)
    print("DEMO 3: Complete RAG Pipeline")
    print("="*60)

    user_content = """
    New research shows that remote work increases productivity by 25% compared to office work.
    The study followed 1000 employees across 6 months, measuring output quality and quantity.
    Key factors: fewer interruptions, flexible schedules, and reduced commute stress.
    Companies adopting remote-first policies report higher employee satisfaction and lower turnover.
    """

    sandbox.demonstrate_rag_pipeline(user_content, "linkedin_post")

    print("\n🎓 Tutorial Complete!")
    print("\n💡 Key Takeaways:")
    print("1. Vectors capture semantic meaning of text")
    print("2. PostgreSQL + pgvector provides fast similarity search")
    print("3. RAG = Retrieve relevant examples + Augment prompts + Generate content")
    print("4. Quality of examples directly impacts output quality")
    print("5. Similarity scores help you tune retrieval relevance")

    print("\n🔧 Integration with your pipeline:")
    print("- Modify choose_format() to retrieve format examples")
    print("- Update write_summary() to use examples as context")
    print("- Store Google Docs examples in this vector database")
    print("- Use format_type + content similarity for best results")

if __name__ == "__main__":
    main()