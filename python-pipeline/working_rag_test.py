#!/usr/bin/env python3
"""
Working RAG Test
================

Test vector similarity search with proper data handling
"""

import os
import numpy as np
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def working_rag_query(query_text: str, top_k: int = 3):
    """Working RAG query with proper embedding handling"""

    # Initialize clients
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    print(f"🔍 Query: '{query_text}'")
    print("=" * 50)

    try:
        # Generate query embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query_text
        )
        query_embedding = np.array(response.data[0].embedding)

        # Get all format examples with embeddings
        result = supabase.table('format_examples').select('*').execute()
        examples = result.data

        # Calculate similarities
        similarities = []
        for example in examples:
            embedding_data = example.get('embedding')
            if embedding_data:
                # Handle different embedding storage formats
                if isinstance(embedding_data, list):
                    example_embedding = np.array(embedding_data)
                elif isinstance(embedding_data, str):
                    # Skip string embeddings for now
                    continue
                else:
                    example_embedding = np.array(embedding_data)

                similarity = cosine_similarity(query_embedding, example_embedding)
                similarities.append({
                    'example': example,
                    'similarity': similarity
                })

        if not similarities:
            print("❌ No valid embeddings found")
            return []

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Show top results
        print(f"✅ Found {len(similarities)} examples, showing top {min(top_k, len(similarities))}:")

        for i, item in enumerate(similarities[:top_k], 1):
            example = item['example']
            similarity = item['similarity']

            print(f"\n{i}. [{example['format_type']}] {example['title']}")
            print(f"   📊 Similarity: {similarity:.3f}")
            print(f"   📝 Preview: {example['content'][:120]}...")

        return similarities[:top_k]

    except Exception as e:
        print(f"❌ RAG query failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_embedding_format():
    """Debug embedding storage format"""

    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    result = supabase.table('format_examples').select('id, title, embedding').limit(1).execute()

    if result.data:
        example = result.data[0]
        embedding = example['embedding']
        print(f"📊 Embedding type: {type(embedding)}")
        print(f"📊 Embedding length: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
        if isinstance(embedding, list) and len(embedding) > 0:
            print(f"📊 First few values: {embedding[:5]}")
        else:
            print(f"📊 Embedding value: {str(embedding)[:100]}...")

if __name__ == "__main__":
    # First, check embedding format
    print("🔍 Checking embedding format...")
    test_embedding_format()
    print("\n" + "="*80 + "\n")

    # Test queries relevant to your content
    test_queries = [
        "content that converts leads into sales",
        "overcoming sales objections",
        "content marketing myths"
    ]

    for query in test_queries:
        working_rag_query(query)
        print("\n" + "="*80 + "\n")