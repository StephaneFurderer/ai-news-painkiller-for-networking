#!/usr/bin/env python3
"""
Final RAG Test
==============

Parse embeddings correctly and test similarity search
"""

import os
import ast
import numpy as np
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def parse_embedding(embedding_str):
    """Parse embedding string to numpy array"""
    try:
        # Try to parse as Python list string
        embedding_list = ast.literal_eval(embedding_str)
        return np.array(embedding_list)
    except:
        return None

def final_rag_query(query_text: str, top_k: int = 3):
    """Final working RAG query"""

    # Initialize clients
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    print(f"🔍 Query: '{query_text}'")
    print("=" * 60)

    try:
        # Generate query embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query_text
        )
        query_embedding = np.array(response.data[0].embedding)

        # Get all format examples
        result = supabase.table('format_examples').select('*').execute()
        examples = result.data

        # Calculate similarities
        similarities = []
        for example in examples:
            embedding_str = example.get('embedding')
            if embedding_str:
                example_embedding = parse_embedding(embedding_str)
                if example_embedding is not None:
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
        print(f"✅ Found {len(similarities)} examples with valid embeddings")
        print(f"🎯 Top {min(top_k, len(similarities))} most similar:")

        for i, item in enumerate(similarities[:top_k], 1):
            example = item['example']
            similarity = item['similarity']

            print(f"\n{i}. [{example['format_type'].upper()}] {example['title']}")
            print(f"   📊 Similarity: {similarity:.3f}")
            print(f"   📝 {example['content'][:200]}...")
            print(f"   ─" * 50)

        return similarities[:top_k]

    except Exception as e:
        print(f"❌ RAG query failed: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # Test queries that should match your content
    test_queries = [
        "how to convert content into sales",
        "dealing with customer objections",
        "myths about content marketing",
        "storytelling in business",
        "content strategy frameworks"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 TEST {i}/{len(test_queries)}")
        final_rag_query(query, top_k=2)
        print("\n" + "="*80)