#!/usr/bin/env python3
"""
Add Embeddings to Existing Format Examples
==========================================

Generate embeddings for format examples that don't have them yet.
"""

import os
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def add_missing_embeddings():
    """Add embeddings to format examples that don't have them"""

    # Initialize clients
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    print("🔍 Checking for examples without embeddings...")

    # Get all format examples
    result = supabase.table('format_examples').select('*').execute()
    examples = result.data

    missing_embeddings = [ex for ex in examples if not ex.get('embedding')]

    print(f"📊 Found {len(missing_embeddings)} examples without embeddings")

    for i, example in enumerate(missing_embeddings, 1):
        print(f"\n{i}/{len(missing_embeddings)} Processing: {example['title']}")

        try:
            # Generate embedding
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=example['content']
            )
            embedding = response.data[0].embedding

            # Update the record
            supabase.table('format_examples').update({
                'embedding': embedding
            }).eq('id', example['id']).execute()

            print(f"   ✅ Embedding added")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print(f"\n🎉 Embeddings update complete!")

    # Verify all examples now have embeddings
    result = supabase.table('format_examples').select('*').execute()
    examples = result.data

    with_embeddings = [ex for ex in examples if ex.get('embedding')]
    print(f"📊 Examples with embeddings: {len(with_embeddings)}/{len(examples)}")

if __name__ == "__main__":
    add_missing_embeddings()