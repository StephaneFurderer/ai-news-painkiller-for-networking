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

from dotenv import load_dotenv
load_dotenv()

from src.tools.data_models import SetGoalType, RefineICPType, CombinedMetadata, AddProofType, ChooseFormatType, WriterOutputType
from src.tools.readwise_client import ReadwiseDocument
from openai import OpenAI
import os
import logging

from src.tools.readwise_client import ReadwiseClient
from src.tools.prompts_utils import SET_GOAL_SYSTEM_PROMPT, REFINE_ICP_SYSTEM_PROMPT,CHOOSE_FORMAT_SYSTEM_PROMPT,REVIEW_WRITER_CONTENT_SYSTEM_PROMPT
from src.tools.html_utils import build_readable_snippet
# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# set openai client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))





# ----------------------------
# Step 1: Retrieve document with Readwise client
# ----------------------------
def retrieve_document(document_id: str) -> ReadwiseDocument:
    """
    Step 1: Retrieve document metadata and HTML content from Readwise

    Returns a dictionary with:
    - title, author, url (metadata)
    - html_content (full HTML)
    """
    try:
        print(f"   Fetching document {document_id} with HTML content...")

        client = ReadwiseClient()
        document = client.get_document_content(document_id, include_html=True)

        if not document:
            print(f" ❌ Document {document_id} not found")
            return None

        print(f" Retrieved: {document.title} ({document.word_count} words)")
        print(f" Author: {document.author}")
        print(f" URL: {document.url}")
        # print the first 100 characters of the content
        print(f" Content: {document.html_content[:100]}...")

        return document

    except Exception as e:
        print(f"   ❌ Error retrieving document: {e}")
        return None

# ----------------------------
# Step 2: Process document with LLM based on the specified task
# ----------------------------

def set_goal(document: ReadwiseDocument) -> SetGoalType:
    """Set Goal Type: Determine the type of content to create"""
    logger.info("Setting goal for content creation")

    model = "gpt-4o-mini"
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SET_GOAL_SYSTEM_PROMPT,
            },
            {"role": "user", "content": f"Title: {document.title}\nAuthor: {document.author}\nURL: {document.url}\n\nHTML snippet:\n{document.html_content[:200]}"},
        ],
        response_format=SetGoalType,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Request routed as: {result.request_type} with confidence: {result.confidence_score}"
    )
    return result

def refine_icp(document: ReadwiseDocument, goal: SetGoalType) -> RefineICPType:
    """Refine the ICP based on the document and the goal"""
    logger.info("Refining ICP")
    model = "gpt-4o-mini"
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": REFINE_ICP_SYSTEM_PROMPT,
            },
            {"role": "user", "content": f"Title: {document.title}\nAuthor: {document.author}\nURL: {document.url}\n\nHTML content:\n{document.html_content}\n\nGoal: {goal.request_type}"},
        ],
        response_format=RefineICPType,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"found ICP: {result.problem} {result.takeaway} {result.change} {result.wondering}"
    )
    return result


def add_proof(state: CombinedMetadata, proof_type = None) -> AddProofType:
    """Add proof to the content"""
    logger.info("Adding proof to the content")
    if proof_type is None:
        proof_type = "external_sources"
        proof = "use the article as the external source"
    else:
        print("we need to implement this part of the code based on a database of proofs points from the end user. Need human in the loop here")
        proof = ""
    return AddProofType(proof_type=proof_type, proof=proof, confidence_score=0.5, reasoning="")

def choose_format(state: CombinedMetadata) -> ChooseFormatType:
    """Choose the format for the content"""
    logger.info("Choosing the format for the content")
    model = "gpt-4o-mini"
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": CHOOSE_FORMAT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": f"Title: {state.title}\nAuthor: {state.author}\nURL: {state.url}\n\nHTML content:\n{state.html_snippet or ''}\n\nGoal: {state.goal}\nICP: {state.icp}"},
        ],
        response_format=ChooseFormatType,
    )
    result = completion.choices[0].message.parsed
    logger.info(f"found format: {result.format_type} {result.format_description}")
    return result


def write_summary(state: CombinedMetadata) -> WriterOutputType:
    """Generate a thoughtful summary using the full HTML content.

    Note: We intentionally pass the full HTML (no truncation) so the model
    can leverage full context.
    """
    logger.info("Writing thoughtful summary from full HTML")
    model = "gpt-4o-mini"
    full_html = state.html_full or ""
    goal_str = state.goal.model_dump_json() if state.goal else "{}"
    icp_str = state.icp.model_dump_json() if state.icp else "{}"
    proof_str = state.proof.model_dump_json() if state.proof else "{}"
    format_str = state.format.model_dump_json() if state.format else "{}"

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a precise summarization and synthesis assistant. Read the full HTML and produce a thoughtful, well-structured summary capturing key insights, evidence, and implications.",
            },
            {
                "role": "user",
                "content": f"Title: {state.title}\nAuthor: {state.author}\nURL: {state.url}\n\nGoal: {goal_str}\nICP: {icp_str}\nProof: {proof_str}\nFormat: {format_str}\n\nFULL_HTML:\n{full_html}",
            },
        ],
        response_format=WriterOutputType,
    )
    result = completion.choices[0].message.parsed
    return result

def review_writer_content(state: CombinedMetadata) -> WriterOutputType:
    """Review the writer content"""
    logger.info("Reviewing the writer content")
    model = "gpt-5-mini"
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": REVIEW_WRITER_CONTENT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": f"writer content: {(state.writer_draft.summary if state.writer_draft else (state.writer_output.summary if state.writer_output else ''))}"},
        ],
        response_format=WriterOutputType,
    )
    result = completion.choices[0].message.parsed
    return result

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

    print(f"✅ Retrieved: {document.title}")

    # Step 2: Process with LLM
    print("Step 2: Set goal...")
    result_set_goal = set_goal(document)

    print("Step 3: Refine ICP...")
    result_refine_icp = refine_icp(document, result_set_goal)
    # Initialize workflow state once, then immutably update via model_copy
    # Build a readable snippet from HTML for prompting
    readable_snippet = build_readable_snippet(document.html_content or document.content or "", url=document.url, max_chars=700)

    state = CombinedMetadata(
        document_id=document.id,
        title=document.title,
        author=document.author,
        url=document.url,
        html_snippet=readable_snippet or (document.html_content[:500] if document.html_content else None),
        html_full=document.html_content or document.content or "",
        goal=result_set_goal,
        icp=result_refine_icp,
    )

    print("Step 4: Add proof...")
    result_add_proof = add_proof(state, "external_sources")
    state = state.model_copy(update={"proof": result_add_proof})

    print("Step 5: Choose format...")
    result_choose_format = choose_format(state)
    state = state.model_copy(update={"format": result_choose_format})

    print("Step 6: Writer - thoughtful summary (full HTML)...")
    writer_output = write_summary(state)
    state = state.model_copy(update={"writer_draft": writer_output, "writer_output": writer_output})

    print("Step 7: Review writer content...")
    result_review_writer_content = review_writer_content(state)
    state = state.model_copy(update={"writer_review": result_review_writer_content, "writer_output": result_review_writer_content})

    print("✅ Processing complete!")
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    print(state.model_dump_json(indent=2))





if __name__ == "__main__":
    main()