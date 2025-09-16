#!/usr/bin/env python3
"""
Readwise Document Processor

A step-by-step app that:
1. Takes a Readwise document ID
2. Retrieves metadata and HTML content
3. Processes it with an LLM

Usage: python readwise_processor.py --document-id "your-doc-id"
"""

import sys
import os
import argparse

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import settings
from tools.readwise_client import ReadwiseClient


# ----------------------------
# Step 1: Retrieve document with Readwise client
# ----------------------------
def retrieve_document(document_id: str) -> dict:
    """
    Step 1: Retrieve document metadata and HTML content from Readwise

    Returns a dictionary with:
    - title, author, url (metadata)
    - html_content (full HTML)
    """
    try:
        print(f"   Fetching document {document_id} with HTML content...")

        client = ReadwiseClient(api_token=settings.readwise_token)
        document = client.get_document_content(document_id, include_html=True)

        if not document:
            print(f" ❌ Document {document_id} not found")
            return None

        print(f" Retrieved: {document.title} ({document.word_count} words)")
        print(f" Author: {document.author}")
        print(f" URL: {document.url}")
        # print the first 100 characters of the content
        print(f" Content: {document.html_content[:100]}...")

        # Convert to simple dict for easier processing
        return {
            "id": document.id,
            "title": document.title,
            "author": document.author,
            "url": document.url,
            "source": document.source,
            "word_count": document.word_count,
            "content": document.content,
            "html_content": document.html_content,
            "summary": document.summary,
            "tags": document.tags
        }

    except Exception as e:
        print(f"   ❌ Error retrieving document: {e}")
        return None

# ----------------------------
# Step 2: Process document with LLM based on the specified task
# ----------------------------

def process_document(document: dict, task: str) -> str:
    """
    Step 2: Process document with LLM based on the specified task

    Args:
        document: Document data from retrieve_document()
        task: Task to perform (summarize, extract-key-points, etc.)

    Returns:
        Processed result as string
    """
    # We'll implement this next
    print(f"   Processing '{document['title']}' for task: {task}")

    # Placeholder for now
    return f"Processed {document['title']} for {task} task"

# ----------------------------
# Main entry point
# ----------------------------
def main():
    """Main entry point for the Readwise processor."""
    parser = argparse.ArgumentParser(description="Process a Readwise document with AI")
    parser.add_argument(
        "--document-id",
        type=str,
        required=True,
        help="Readwise document ID to process"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="summarize",
        choices=["summarize", "extract-key-points", "analyze-sentiment"],
        help="Task to perform on the document"
    )

    args = parser.parse_args()

    print(f"🔍 Processing Readwise document: {args.document_id}")
    print(f"📋 Task: {args.task}")
    print("=" * 50)

    # Step 1: Retrieve document
    print("Step 1: Retrieving document...")
    document = retrieve_document(args.document_id)

    if not document:
        print("❌ Failed to retrieve document")
        return

    print(f"✅ Retrieved: {document['title']}")

    # Step 2: Process with LLM
    print("Step 2: Processing with LLM...")
    result = process_document(document, args.task)

    print("✅ Processing complete!")
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    print(result)





if __name__ == "__main__":
    main()