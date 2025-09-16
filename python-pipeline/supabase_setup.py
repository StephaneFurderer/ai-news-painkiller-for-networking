#!/usr/bin/env python3
"""
Supabase Setup and Migration Script
==================================

This script will:
1. Set up your Supabase database schema
2. Migrate data from local PostgreSQL
3. Test the connection and vector operations
4. Show you how to use the Supabase dashboard

Prerequisites:
- Supabase account and project created
- pip install supabase python-dotenv
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional
from openai import OpenAI

load_dotenv()

class SupabaseRAGSetup:
    def __init__(self):
        """Initialize Supabase client"""

        # Get credentials from environment
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")  # or SERVICE_ROLE_KEY for admin operations

        if not self.supabase_url or not self.supabase_key:
            print("❌ Missing Supabase credentials!")
            print("💡 Add to your .env file:")
            print("SUPABASE_URL=https://your-project.supabase.co")
            print("SUPABASE_ANON_KEY=your-anon-key")
            return

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print("✅ Connected to Supabase!")

    def setup_database_schema(self):
        """Create the database schema via SQL"""

        print("🔧 Setting up database schema...")

        # Enable pgvector extension
        try:
            self.supabase.rpc('enable_pgvector').execute()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️  pgvector extension: {e}")
            print("💡 This is normal if already enabled")

        # Create tables via SQL
        # Note: We'll use Supabase SQL Editor for this as it's easier
        schema_sql = """
        -- Enable pgvector if not already enabled
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Articles table (your processed Readwise content)
        CREATE TABLE IF NOT EXISTS articles (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            readwise_id text UNIQUE,
            title text NOT NULL,
            author text,
            url text,
            content text,
            html_content text,
            word_count integer DEFAULT 0,

            -- Processing results from your pipeline
            goal jsonb,
            icp jsonb,
            proof jsonb,
            format jsonb,
            writer_output jsonb,
            processed_summary text,

            -- Vector for similarity search
            embedding vector(1536),

            -- Metadata
            tags text[],
            source text DEFAULT 'readwise',
            processing_status text DEFAULT 'pending',

            created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
            updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
        );

        -- Format examples table (from Google Docs)
        CREATE TABLE IF NOT EXISTS format_examples (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            format_type text NOT NULL,
            title text,
            content text NOT NULL,

            -- Source tracking
            source_doc_id text,  -- Google Doc ID
            source_url text,     -- Google Doc URL

            -- Vector for RAG retrieval
            embedding vector(1536),

            -- Metadata for filtering and organization
            metadata jsonb DEFAULT '{}',

            -- Usage tracking
            usage_count integer DEFAULT 0,
            last_used_at timestamp with time zone,

            created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
            updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
        );

        -- Create indexes for fast vector similarity search
        CREATE INDEX IF NOT EXISTS articles_embedding_idx ON articles
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

        CREATE INDEX IF NOT EXISTS format_examples_embedding_idx ON format_examples
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

        -- Additional indexes for common queries
        CREATE INDEX IF NOT EXISTS articles_readwise_id_idx ON articles (readwise_id);
        CREATE INDEX IF NOT EXISTS articles_created_at_idx ON articles (created_at DESC);
        CREATE INDEX IF NOT EXISTS format_examples_format_type_idx ON format_examples (format_type);

        -- Enable Row Level Security (RLS) - good practice
        ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE format_examples ENABLE ROW LEVEL SECURITY;

        -- Create policies (for now, allow all operations - adjust later for auth)
        CREATE POLICY IF NOT EXISTS "Allow all operations on articles" ON articles FOR ALL USING (true);
        CREATE POLICY IF NOT EXISTS "Allow all operations on format_examples" ON format_examples FOR ALL USING (true);

        -- Create updated_at trigger function
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc'::text, now());
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Add triggers to update updated_at automatically
        CREATE TRIGGER IF NOT EXISTS update_articles_updated_at BEFORE UPDATE ON articles
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER IF NOT EXISTS update_format_examples_updated_at BEFORE UPDATE ON format_examples
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """

        print("\n📋 Copy this SQL to your Supabase SQL Editor:")
        print("=" * 60)
        print(schema_sql)
        print("=" * 60)
        print("\n🔗 Go to: https://supabase.com/dashboard/project/your-project-id/sql")
        print("1. Paste the SQL above")
        print("2. Click 'Run'")
        print("3. Come back here and press Enter")
        input("\nPress Enter when you've run the SQL in Supabase...")

        print("✅ Database schema should be created!")

    def test_connection(self):
        """Test basic Supabase operations"""

        print("\n🧪 Testing Supabase connection...")

        try:
            # Test basic query
            result = self.supabase.table('articles').select('*').limit(1).execute()
            print("✅ Can query articles table")

            result = self.supabase.table('format_examples').select('*').limit(1).execute()
            print("✅ Can query format_examples table")

            print("🎉 Supabase connection working perfectly!")
            return True

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def migrate_local_data(self):
        """Migrate data from your local PostgreSQL sandbox"""

        print("\n📦 Ready to migrate your local data?")
        print("This will copy format examples from your local PostgreSQL to Supabase")

        migrate = input("Proceed with migration? (y/n): ").lower() == 'y'
        if not migrate:
            print("⏭️  Skipping migration")
            return

        # Import local database connection
        try:
            import psycopg2

            # Connect to local database (same config as sandbox)
            local_conn = psycopg2.connect(
                host='localhost',
                database='vector_sandbox',
                user='sf',
                password='',
                port=5432
            )

            # Fetch data from local database
            with local_conn.cursor() as cur:
                cur.execute("SELECT format_type, example_title, content, embedding, metadata FROM format_examples")
                local_data = cur.fetchall()

            print(f"📊 Found {len(local_data)} format examples in local database")

            # Insert into Supabase
            for row in local_data:
                format_type, title, content, embedding, metadata = row

                # Convert embedding list to proper format
                embedding_list = embedding if isinstance(embedding, list) else list(embedding)

                # Convert metadata if it's a string
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                data = {
                    'format_type': format_type,
                    'title': title,
                    'content': content,
                    'embedding': embedding_list,
                    'metadata': metadata or {}
                }

                try:
                    result = self.supabase.table('format_examples').insert(data).execute()
                    print(f"✅ Migrated: {title}")
                except Exception as e:
                    print(f"❌ Failed to migrate {title}: {e}")

            print("🎉 Migration complete!")

        except ImportError:
            print("⚠️  psycopg2 not available - skipping migration")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

    def add_sample_article(self):
        """Add a sample processed article to test the full pipeline"""

        print("\n📝 Adding sample article...")

        sample_content = """
        Recent studies show that remote work increases productivity by 25% compared to traditional office environments.
        The research, conducted across 1,000 employees over 6 months, measured both output quality and quantity.
        Key productivity factors identified include: fewer workplace interruptions, flexible scheduling that matches
        individual peak performance hours, and reduced commute-related stress and fatigue.
        """

        # Generate embedding for the article
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=sample_content
            )
            embedding = response.data[0].embedding

            # Sample article data (simulating your pipeline output)
            article_data = {
                'readwise_id': 'sample_001',
                'title': 'Remote Work Productivity Study: 25% Increase in Output',
                'author': 'Research Institute',
                'url': 'https://example.com/remote-work-study',
                'content': sample_content,
                'word_count': len(sample_content.split()),
                'goal': {
                    'request_type': 'linkedin_post',
                    'confidence_score': 0.9,
                    'reasoning': 'Professional audience would benefit from productivity insights'
                },
                'icp': {
                    'problem': 'Remote work productivity concerns',
                    'takeaway': 'Data-driven evidence of remote work benefits',
                    'change': 'Shift perception from skeptical to supportive',
                    'wondering': 'How to implement effective remote work policies'
                },
                'processed_summary': 'Remote work study reveals 25% productivity boost through reduced interruptions and flexible scheduling.',
                'embedding': embedding,
                'tags': ['remote-work', 'productivity', 'research', 'workplace'],
                'processing_status': 'completed'
            }

            result = self.supabase.table('articles').insert(article_data).execute()
            print("✅ Sample article added successfully!")

            return result.data[0]['id'] if result.data else None

        except Exception as e:
            print(f"❌ Failed to add sample article: {e}")
            return None

    def test_rag_query(self, article_id: Optional[str] = None):
        """Test RAG functionality with Supabase"""

        print("\n🔍 Testing RAG functionality...")

        # Test query
        query_text = "productivity tips for remote workers"

        try:
            # Generate query embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query_text
            )
            query_embedding = response.data[0].embedding

            # Search for similar format examples using Supabase RPC
            # Note: We'll need to create this RPC function in Supabase
            similar_examples = self.supabase.rpc(
                'match_format_examples',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': 3
                }
            ).execute()

            if similar_examples.data:
                print(f"✅ Found {len(similar_examples.data)} similar examples")
                for example in similar_examples.data:
                    print(f"   📄 {example.get('title', 'Untitled')} (similarity: {example.get('similarity', 0):.3f})")
            else:
                print("ℹ️  No similar examples found (this is normal for a fresh database)")

            # Search for similar articles
            similar_articles = self.supabase.rpc(
                'match_articles',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': 3
                }
            ).execute()

            if similar_articles.data:
                print(f"✅ Found {len(similar_articles.data)} similar articles")
                for article in similar_articles.data:
                    print(f"   📰 {article.get('title', 'Untitled')} (similarity: {article.get('similarity', 0):.3f})")
            else:
                print("ℹ️  No similar articles found")

        except Exception as e:
            print(f"⚠️  RAG test incomplete: {e}")
            print("💡 You'll need to create the RPC functions - I'll show you how next")

    def create_rpc_functions(self):
        """Show SQL for creating RPC functions for vector similarity"""

        rpc_sql = """
        -- Function to search for similar format examples
        CREATE OR REPLACE FUNCTION match_format_examples (
            query_embedding vector(1536),
            match_threshold float,
            match_count int
        )
        RETURNS TABLE (
            id uuid,
            format_type text,
            title text,
            content text,
            metadata jsonb,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                format_examples.id,
                format_examples.format_type,
                format_examples.title,
                format_examples.content,
                format_examples.metadata,
                1 - (format_examples.embedding <=> query_embedding) as similarity
            FROM format_examples
            WHERE 1 - (format_examples.embedding <=> query_embedding) > match_threshold
            ORDER BY format_examples.embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;

        -- Function to search for similar articles
        CREATE OR REPLACE FUNCTION match_articles (
            query_embedding vector(1536),
            match_threshold float,
            match_count int
        )
        RETURNS TABLE (
            id uuid,
            readwise_id text,
            title text,
            content text,
            processed_summary text,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                articles.id,
                articles.readwise_id,
                articles.title,
                articles.content,
                articles.processed_summary,
                1 - (articles.embedding <=> query_embedding) as similarity
            FROM articles
            WHERE 1 - (articles.embedding <=> query_embedding) > match_threshold
            ORDER BY articles.embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;
        """

        print("\n🔧 Add these RPC functions to your Supabase SQL Editor:")
        print("=" * 60)
        print(rpc_sql)
        print("=" * 60)

    def show_dashboard_tour(self):
        """Guide user through Supabase dashboard features"""

        print("\n🎯 Supabase Dashboard Tour")
        print("=" * 40)

        print("\n📊 Table Editor:")
        print("- View/edit your articles and format_examples")
        print("- Filter, sort, and search your data")
        print("- Add new records manually")

        print("\n🔍 SQL Editor:")
        print("- Write custom queries")
        print("- Test vector similarity searches")
        print("- Create charts from query results")

        print("\n📈 Database Analytics:")
        print("- Monitor database size and usage")
        print("- Track API requests")
        print("- View performance metrics")

        print("\n🔗 API Documentation:")
        print("- Auto-generated REST API docs")
        print("- Test API endpoints directly")
        print("- Get code snippets for your app")

        print("\n📋 Useful queries to try in SQL Editor:")
        print("""
        -- View all articles
        SELECT title, author, processing_status, created_at FROM articles;

        -- View format examples by type
        SELECT format_type, count(*) as count FROM format_examples GROUP BY format_type;

        -- Test vector similarity (replace with actual embedding)
        SELECT title, 1 - (embedding <=> '[0,0,0...]'::vector) as similarity
        FROM articles
        ORDER BY embedding <=> '[0,0,0...]'::vector
        LIMIT 5;
        """)

def main():
    """Main setup flow"""

    print("🚀 Supabase RAG Setup")
    print("=" * 30)

    print("\n📋 Prerequisites checklist:")
    print("✅ Supabase account created at supabase.com")
    print("✅ New project created in Supabase dashboard")
    print("✅ Environment variables added to .env file")
    print("\nIf you haven't done these steps, please complete them first!")

    ready = input("\nReady to proceed? (y/n): ").lower() == 'y'
    if not ready:
        print("👋 Come back when you're ready!")
        return

    # Initialize setup
    setup = SupabaseRAGSetup()
    if not hasattr(setup, 'supabase'):
        return

    # Run setup steps
    setup.setup_database_schema()

    if setup.test_connection():
        setup.migrate_local_data()
        article_id = setup.add_sample_article()
        setup.create_rpc_functions()
        setup.test_rag_query(article_id)
        setup.show_dashboard_tour()

        print("\n🎉 Setup Complete!")
        print("\n🔗 Next steps:")
        print("1. Explore your Supabase dashboard")
        print("2. Run the RPC functions SQL in SQL Editor")
        print("3. Test queries in Table Editor")
        print("4. Ready to integrate with your pipeline!")
    else:
        print("❌ Setup incomplete - check your Supabase configuration")

if __name__ == "__main__":
    main()