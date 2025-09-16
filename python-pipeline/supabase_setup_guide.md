# Supabase Setup Guide

## Step 1: Create Supabase Account & Project

1. **Go to [supabase.com](https://supabase.com)**
2. **Sign up/Sign in** (free account)
3. **Create New Project**:
   - Name: `ai-news-rag`
   - Database password: (save this!)
   - Region: Choose closest to you
4. **Wait for project creation** (~2 minutes)

## Step 2: Get Your Credentials

1. **Go to Project Settings** → **API**
2. **Copy these values**:
   - **Project URL**: `https://your-project-id.supabase.co`
   - **Anon public key**: `eyJhbGciOiJIUzI1...` (long string)

## Step 3: Add to Your .env File

Add these lines to your `.env` file:

```bash
# Add to your existing .env file
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Your existing keys
OPENAI_API_KEY=sk-...
READWISE_TOKEN=...
```

## Step 4: Install Dependencies

```bash
pip install supabase python-dotenv
```

## Step 5: Run Setup Script

```bash
python supabase_setup.py
```

The script will:
- ✅ Connect to your Supabase project
- ✅ Show you SQL to create tables
- ✅ Test the connection
- ✅ Migrate your local data
- ✅ Add sample content
- ✅ Guide you through the dashboard

## Step 6: Explore Supabase Dashboard

After setup, visit your dashboard:

### 📊 Table Editor
- **URL**: `https://supabase.com/dashboard/project/your-project-id/editor`
- **What you'll see**: Your articles and format_examples tables
- **Try**: Add a new format example manually

### 🔍 SQL Editor
- **URL**: `https://supabase.com/dashboard/project/your-project-id/sql`
- **What you'll see**: Query interface with syntax highlighting
- **Try**: `SELECT * FROM articles;`

### 📈 Analytics
- **URL**: `https://supabase.com/dashboard/project/your-project-id/reports`
- **What you'll see**: Database usage, API requests, performance

### 🔗 API Docs
- **URL**: `https://supabase.com/dashboard/project/your-project-id/api`
- **What you'll see**: Auto-generated REST API documentation
- **Try**: Test an API endpoint

## Database Schema Overview

```sql
articles (
  id uuid PRIMARY KEY,
  readwise_id text UNIQUE,
  title text,
  content text,
  processed_summary text,
  embedding vector(1536),  -- For similarity search
  goal jsonb,              -- Your pipeline output
  icp jsonb,
  processing_status text,
  created_at timestamp
)

format_examples (
  id uuid PRIMARY KEY,
  format_type text,        -- 'linkedin_post', 'twitter_thread', etc.
  content text,
  embedding vector(1536),  -- For RAG retrieval
  source_doc_id text,      -- Google Doc ID
  metadata jsonb,
  created_at timestamp
)
```

## Key Features You Get

### 🔍 Semantic Search
```sql
-- Find articles similar to a topic
SELECT title, similarity
FROM match_articles('[your_embedding_vector]', 0.7, 5);
```

### 📊 Analytics Queries
```sql
-- Most common format types
SELECT format_type, count(*)
FROM format_examples
GROUP BY format_type;

-- Recent articles
SELECT title, created_at
FROM articles
ORDER BY created_at DESC
LIMIT 10;
```

### 🚀 Real-time Updates
- Any changes to your database appear instantly in dashboard
- Perfect for monitoring your RAG system

## Next Steps

1. ✅ **Complete setup script**
2. ✅ **Explore dashboard**
3. ✅ **Test vector queries**
4. 🔄 **Integrate with your pipeline**
5. 🌐 **Deploy to production**

## Troubleshooting

### Can't connect to Supabase
- ✅ Check your `.env` file has correct URL and key
- ✅ Make sure project is fully created (not still initializing)

### pgvector not working
- ✅ Run the schema SQL in SQL Editor first
- ✅ pgvector is pre-installed in Supabase (should work automatically)

### Migration fails
- ✅ Make sure local PostgreSQL is running
- ✅ Check local database credentials in setup script

### No data showing
- ✅ Run the setup script completely
- ✅ Check Table Editor for your tables
- ✅ Try adding sample data manually

## Free Tier Limits

- ✅ **Database**: 500MB storage
- ✅ **API requests**: 50,000 per month
- ✅ **Auth users**: 50,000 per month
- ✅ **Realtime**: 200 concurrent connections

Perfect for personal RAG projects!