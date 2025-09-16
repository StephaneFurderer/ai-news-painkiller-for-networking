#!/usr/bin/env python3
"""
CSV Format Examples Loader
=========================

Load format examples from a CSV file into Supabase.
Much easier than hardcoding examples!
"""

import os
import csv
import json
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def load_csv_to_supabase(csv_file: str):
    """Load format examples from CSV to Supabase"""

    # Initialize clients
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"📂 Loading examples from {csv_file}")

    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for i, row in enumerate(reader, 1):
                format_type = row['format_type']
                title = row['title']
                content = row['content']

                # Parse metadata JSON
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except json.JSONDecodeError:
                    metadata = {}

                print(f"\n{i}. Processing: {title} ({format_type})")

                # Generate embedding
                try:
                    response = openai_client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=content
                    )
                    embedding = response.data[0].embedding
                    print("   ✅ Embedding generated")

                    # Insert into Supabase
                    result = supabase.table('format_examples').insert({
                        'format_type': format_type,
                        'title': title,
                        'content': content,
                        'embedding': embedding,
                        'metadata': metadata
                    }).execute()

                    print("   ✅ Saved to database")

                except Exception as e:
                    print(f"   ❌ Failed: {e}")

        print(f"\n🎉 CSV loading complete!")

        # Show final count
        result = supabase.table('format_examples').select('*').execute()
        print(f"📊 Total examples in database: {len(result.data)}")

    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")

if __name__ == "__main__":
    load_csv_to_supabase("format_examples.csv")