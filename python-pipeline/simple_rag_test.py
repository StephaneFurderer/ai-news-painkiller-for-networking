#!/usr/bin/env python3
"""
Simple RAG Test
===============

Test vector similarity search without RPC functions
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

def simple_rag_query(query_text: str, top_k: int = 3):
    """Simple RAG query using cosine similarity"""

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
            if example.get('embedding'):
                example_embedding = np.array(example['embedding'])
                similarity = cosine_similarity(query_embedding, example_embedding)
                similarities.append({
                    'example': example,
                    'similarity': similarity
                })

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Show top results
        print(f"✅ Found {len(similarities)} examples, showing top {top_k}:")

        for i, item in enumerate(similarities[:top_k], 1):
            example = item['example']
            similarity = item['similarity']

            print(f"\n{i}. {example['format_type']} - {example['title']}")
            print(f"   Similarity: {similarity:.3f}")
            print(f"   Preview: {example['content'][:150]}...")

        return similarities[:top_k]

    except Exception as e:
        print(f"❌ RAG query failed: {e}")
        return []

if __name__ == "__main__":
    # Test queries relevant to your content
    test_queries = [
        "content that converts leads into sales",
        "overcoming sales objections",
        "content marketing myths",
        "personal stories for business",
        "frameworks for better content"
    ]

    for query in test_queries:
        simple_rag_query(query)
        print("\n" + "="*80 + "\n")