#!/usr/bin/env python3
"""
RAG-Enhanced Readwise Processor
==============================

Your existing pipeline + RAG format examples for better content generation
"""

import sys
import os
import argparse
import ast
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from src.tools.data_models import SetGoalType, RefineICPType, CombinedMetadata, AddProofType, ChooseFormatType, WriterOutputType
from src.tools.readwise_client import ReadwiseDocument, ReadwiseClient
from openai import OpenAI
from supabase import create_client
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def parse_embedding(embedding_str):
    """Parse embedding string to numpy array"""
    try:
        embedding_list = ast.literal_eval(embedding_str)
        return np.array(embedding_list)
    except:
        return None

def find_similar_format_examples(query_text: str, format_type: str = None, top_k: int = 3):
    """Find similar format examples using RAG"""

    try:
        # Generate query embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query_text
        )
        query_embedding = np.array(response.data[0].embedding)

        # Get format examples (filter by type if specified)
        if format_type:
            result = supabase.table('format_examples').select('*').eq('format_type', format_type).execute()
        else:
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

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []

# Your existing pipeline functions (modified for RAG)

def retrieve_document(document_id: str) -> ReadwiseDocument:
    """Step 1: Retrieve document metadata and HTML content from Readwise"""
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
        print(f" Content: {document.html_content[:100]}...")

        return document

    except Exception as e:
        print(f"   ❌ Error retrieving document: {e}")
        return None

def set_goal(document: ReadwiseDocument) -> SetGoalType:
    """Set Goal Type: Determine the type of content to create"""
    logger.info("Setting goal for content creation")

    # Use existing logic
    from src.tools.prompts_utils import SET_GOAL_SYSTEM_PROMPT

    model = "gpt-4o-mini"
    completion = openai_client.beta.chat.completions.parse(
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
    logger.info(f"Request routed as: {result.request_type} with confidence: {result.confidence_score}")
    return result

def refine_icp(document: ReadwiseDocument, goal: SetGoalType) -> RefineICPType:
    """Refine the ICP based on the document and the goal"""
    logger.info("Refining ICP")

    from src.tools.prompts_utils import REFINE_ICP_SYSTEM_PROMPT

    model = "gpt-4o-mini"
    completion = openai_client.beta.chat.completions.parse(
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
    logger.info(f"found ICP: {result.problem} {result.takeaway} {result.change} {result.wondering}")
    return result

def add_proof(state: CombinedMetadata, proof_type=None) -> AddProofType:
    """Add proof to the content"""
    logger.info("Adding proof to the content")
    if proof_type is None:
        proof_type = "external_sources"
        proof = "use the article as the external source"
    else:
        print("we need to implement this part of the code based on a database of proofs points from the end user. Need human in the loop here")
        proof = ""
    return AddProofType(proof_type=proof_type, proof=proof, confidence_score=0.5, reasoning="")

def choose_format_with_rag(state: CombinedMetadata) -> ChooseFormatType:
    """Choose the format for the content using RAG examples"""
    logger.info("Choosing format with RAG assistance")

    # Create search query from the content context
    search_query = f"{state.title} {state.goal.request_type if state.goal else ''} {state.icp.problem if state.icp else ''}"

    # Find similar format examples
    logger.info(f"🔍 Searching for format examples similar to: '{search_query[:100]}...'")
    similar_examples = find_similar_format_examples(search_query, top_k=3)

    # Build context from similar examples
    examples_context = ""
    if similar_examples:
        logger.info(f"✅ Found {len(similar_examples)} similar format examples")
        examples_context = "\n\nSimilar format examples for inspiration:\n"
        for i, item in enumerate(similar_examples, 1):
            example = item['example']
            similarity = item['similarity']
            examples_context += f"\nExample {i} ({example['format_type']}, similarity: {similarity:.3f}):\n"
            examples_context += f"Title: {example['title']}\n"
            examples_context += f"Content: {example['content'][:300]}...\n"
            examples_context += "---\n"
    else:
        logger.warning("⚠️ No similar format examples found")

    from src.tools.prompts_utils import CHOOSE_FORMAT_SYSTEM_PROMPT

    model = "gpt-4o-mini"
    completion = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": CHOOSE_FORMAT_SYSTEM_PROMPT + examples_context,
            },
            {"role": "user", "content": f"Title: {state.title}\nAuthor: {state.author}\nURL: {state.url}\n\nHTML content:\n{state.html_snippet or ''}\n\nGoal: {state.goal}\nICP: {state.icp}"},
        ],
        response_format=ChooseFormatType,
    )
    result = completion.choices[0].message.parsed
    logger.info(f"found format: {result.format_type} {result.format_description}")
    return result

def write_summary_with_rag(state: CombinedMetadata) -> WriterOutputType:
    """Generate content using RAG format examples with 3-step approach"""
    logger.info("Writing summary with RAG assistance (3-step process)")

    # Search for examples of the chosen format type
    format_type = state.format.format_type if state.format else "general"
    content_context = f"{state.title} {state.icp.problem if state.icp else ''}"

    logger.info(f"🔍 Searching for {format_type} examples similar to: '{content_context[:100]}...'")
    similar_examples = find_similar_format_examples(
        content_context,
        format_type=format_type,
        top_k=2
    )

    if not similar_examples:
        logger.warning("⚠️ No format examples found, using standard approach")
        # Fallback to original method if no examples found
        return write_standard_summary(state)

    # Get the best matching template
    best_example = similar_examples[0]['example']
    template_content = best_example['content']
    logger.info(f"✅ Using template: '{best_example['title']}' (similarity: {similar_examples[0]['similarity']:.3f})")

    model = "gpt-5-mini"
    full_html = state.html_full or ""

    # STEP 1: Generate initial summary draft
    logger.info("📝 Step 1: Generating initial summary draft...")

    draft_prompt = f"""Create a comprehensive summary of this article for {format_type} content.

Focus on the key insights, problems, solutions, and outcomes mentioned in the article.
Write this as a detailed paragraph capturing all important points.

Article content: {full_html}

Title: {state.title}
Goal: {state.goal.request_type if state.goal else 'general'}
Target audience problem: {state.icp.problem if state.icp else 'general audience'}"""

    draft_response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a content summarization expert. Create detailed, comprehensive summaries."},
            {"role": "user", "content": draft_prompt}
        ]
    )

    summary_draft = draft_response.choices[0].message.content
    logger.info(f"✅ Draft created ({len(summary_draft)} chars)")

    # STEP 2: Refine into key points
    logger.info("🔧 Step 2: Refining into key points...")

    refine_prompt = f"""Take this summary draft and refine it into clear, concise key points:

{summary_draft}

Extract the most important insights and present them as:
- Clear, direct statements
- Remove unnecessary words
- Focus on the core message and outcomes
- Keep the essence but make it more impactful"""

    refine_response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert at distilling content into clear, impactful key points."},
            {"role": "user", "content": refine_prompt}
        ]
    )

    refined_points = refine_response.choices[0].message.content
    logger.info(f"✅ Key points extracted ({len(refined_points)} chars)")

    # STEP 3: Apply format template
    logger.info("🎨 Step 3: Applying format template...")

    template_prompt = f"""Use this proven template structure to create the final {format_type} post:

TEMPLATE STRUCTURE:
{template_content}

KEY POINTS TO INCORPORATE:
{refined_points}

ORIGINAL CONTEXT:
- Title: {state.title}
- Target audience: {state.icp.problem if state.icp else 'business professionals'}
- Goal: {state.goal.request_type if state.goal else 'educate and engage'}

INSTRUCTIONS:
1. Follow the EXACT structure and flow of the template
2. Replace the template's content with insights from the key points
3. Maintain the template's tone, style, and formatting
4. Keep the same emotional hooks and transitions
5. Make it specific to the article's topic
6. Ensure it flows naturally and feels authentic

Create the final post that matches the template's proven format while incorporating the article's insights."""

    final_response = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": f"You are an expert at creating {format_type} content using proven templates. Follow the template structure exactly while making the content original and relevant."},
            {"role": "user", "content": template_prompt}
        ],
        response_format=WriterOutputType,
    )

    result = final_response.choices[0].message.parsed
    logger.info("✅ Final templated content created successfully")

    # Log the process for debugging
    logger.info(f"📊 Process summary:")
    logger.info(f"   Template used: {best_example['title']}")
    logger.info(f"   Draft length: {len(summary_draft)} chars")
    logger.info(f"   Refined length: {len(refined_points)} chars")
    logger.info(f"   Final length: {len(result.summary)} chars")

    return result

def write_standard_summary(state: CombinedMetadata) -> WriterOutputType:
    """Fallback method when no format examples are available"""
    model = "gpt-5-mini"
    full_html = state.html_full or ""
    goal_str = state.goal.model_dump_json() if state.goal else "{}"
    icp_str = state.icp.model_dump_json() if state.icp else "{}"
    proof_str = state.proof.model_dump_json() if state.proof else "{}"
    format_str = state.format.model_dump_json() if state.format else "{}"

    completion = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a precise summarization and synthesis assistant. Create engaging, well-structured content.",
            },
            {
                "role": "user",
                "content": f"Title: {state.title}\nAuthor: {state.author}\nURL: {state.url}\n\nGoal: {goal_str}\nICP: {icp_str}\nProof: {proof_str}\nFormat: {format_str}\n\nFULL_HTML:\n{full_html}",
            },
        ],
        response_format=WriterOutputType,
    )
    return completion.choices[0].message.parsed

def review_writer_content(state: CombinedMetadata) -> WriterOutputType:
    """Review the writer content with LinkedIn design principles"""
    logger.info("Reviewing the writer content with design guidelines")

    # LinkedIn Design Principles
    design_principles = """
LINKEDIN POST DESIGN PRINCIPLES:

1. Keep it simple!
2. Stay consistent
3. Don't use emojis
4. Add some rhythm
5. Add lots of spacing
6. Create a logical flow
7. 45 characters per line
8. Use numbered listicles
9. Cut unnecessary words
10. Place ur CTA at the end
11. Adapt for mobile readers
12. Write hooks as one-liners
13. Use AI, but not exclusively
14. Arrange your lists by length
15. Avoid jargon and buzzwords
16. Use frameworks (PAS / AIDA)
17. Present info using bullet points

Good writing grabs attention.
Great formatting keeps it.

Apply these principles to improve the content's visual appeal and readability.
"""

    from src.tools.prompts_utils import REVIEW_WRITER_CONTENT_SYSTEM_PROMPT

    enhanced_system_prompt = f"""{REVIEW_WRITER_CONTENT_SYSTEM_PROMPT}

{design_principles}

Focus on:
- Improving formatting and visual design
- Optimizing line length (aim for 45 characters per line)
- Adding appropriate spacing and rhythm
- Ensuring mobile readability
- Creating logical flow and structure
- Removing unnecessary words
- Making the hook more impactful
"""

    model = "gpt-4o-mini"

    completion = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": enhanced_system_prompt,
            },
            {"role": "user", "content": f"Review and improve this content for LinkedIn formatting and design:\n\n{(state.writer_draft.summary if state.writer_draft else (state.writer_output.summary if state.writer_output else ''))}"},
        ],
        response_format=WriterOutputType,
    )
    result = completion.choices[0].message.parsed
    logger.info("✅ Content reviewed with LinkedIn design principles applied")
    return result

def main():
    """Main entry point for the RAG-enhanced Readwise processor."""
    parser = argparse.ArgumentParser(description="Process a Readwise document with AI + RAG")
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
    print(f"🧠 Enhanced with RAG format examples")
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

    # Build a readable snippet from HTML for prompting
    from src.tools.html_utils import build_readable_snippet
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

    print("Step 5: Choose format with RAG...")
    result_choose_format = choose_format_with_rag(state)
    state = state.model_copy(update={"format": result_choose_format})

    print("Step 6: Write content with RAG examples...")
    writer_output = write_summary_with_rag(state)
    state = state.model_copy(update={"writer_draft": writer_output, "writer_output": writer_output})

    print("Step 7: Review writer content...")
    result_review_writer_content = review_writer_content(state)
    state = state.model_copy(update={"writer_review": result_review_writer_content, "writer_output": result_review_writer_content})

    print("✅ RAG-enhanced processing complete!")
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print("="*50)
    print(f"📝 Title: {state.title}")
    print(f"🎯 Format: {state.format.format_type}")
    print(f"📄 Generated Content:")
    print("-" * 30)
    print(state.writer_output.summary)
    print("-" * 30)

    # Also print full state for debugging
    print("\n" + "="*50)
    print("FULL PIPELINE STATE:")
    print("="*50)
    print(state.model_dump_json(indent=2))

if __name__ == "__main__":
    main()