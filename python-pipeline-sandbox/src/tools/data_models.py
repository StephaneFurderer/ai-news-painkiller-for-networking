
from pydantic import BaseModel, Field
from typing import Literal, Optional

#use pydantic to define the data models

class SetGoalType(BaseModel):
    """Set Goal Type: Determine the type of content to create"""

    request_type: Literal["attract", "nurture", "convert"] = Field(
        description="Type of content to create"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    description: str = Field(description="Cleaned description of the request")
    reasoning: str = Field(description="What am I trying to make happen with this?")

class RefineICPType(BaseModel):
    """Refine ICP Type: Refine the ICP based on the document and the goal"""

    problem: str = Field(description="What problem am I solving?")
    takeaway: str = Field(description="What’s the takeaway for them?")
    change: str = Field(description="What change or result could they get?")
    wondering: str = Field(description="What might they be wondering right now?")


class CombinedMetadata(BaseModel):
    """Workflow state combining document info and step results."""

    # Document metadata
    document_id: str = Field(description="Readwise document ID")
    title: str = Field(description="Document title")
    author: str = Field(description="Document author")
    url: str = Field(description="Document URL")
    html_snippet: Optional[str] = Field(default=None, description="Optional HTML snippet for prompting")
    html_full: Optional[str] = Field(default=None, description="Full HTML content for writer or deep processing")

    # Step outputs (optional until produced)
    goal: Optional[SetGoalType] = Field(default=None, description="Goal routing result")
    icp: Optional[RefineICPType] = Field(default=None, description="Refined ICP result")
    proof: Optional["AddProofType"] = Field(default=None, description="Proof attached to content")
    format: Optional["ChooseFormatType"] = Field(default=None, description="Chosen content format")
    # Writer outputs
    writer_draft: Optional["WriterOutputType"] = Field(default=None, description="First-pass writer draft output")
    writer_review: Optional["WriterOutputType"] = Field(default=None, description="Reviewed/refined writer output")
    # For backward-compat if referenced elsewhere
    writer_output: Optional["WriterOutputType"] = Field(default=None, description="Deprecated: use writer_draft/writer_review")


# Forward references for optional fields above
try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .data_models import AddProofType, ChooseFormatType, WriterOutputType
except Exception:
    pass


class AddProofType(BaseModel):
    """Add Proof Type: Add proof to the content"""
    # by default, use external_sources if no proof is provided
    proof_type: Literal["your_experiences", "client_results", "real_stories", "external_sources"] = Field(description="Type of proof to add to the content", default="external_sources")
    proof: str = Field(description="Proof to add to the content", default="")
    confidence_score: float = Field(description="Confidence score between 0 and 1", default=0.5)
    reasoning: str = Field(description="Reasoning for the proof", default="")

class ChooseFormatType(BaseModel):
    """
    Choose Format Type: Choose the format for the content
    We will have a list of formats to choose from organized as follows given the goal and the ICP:
    Attract (awareness/trust): 
        - belief shift, 
        - origin story, 
        - industry myths
    Nurture (authority/demand): 
        - framework, 
        - step-by-step, 
        - how I / how to
    Convert (qualify/filter): 
        - objection post, 
        - result breakdown, 
        - client success story
    """
    
    format_type: Literal["belief shift", "origin story", "industry myths", "framework", "step-by-step", "how to", "objection post", "result breakdown", "client success story"] = Field(description="Type of format to choose", default="how to")
    format_description: str = Field(description="Description of the format", default="")
    confidence_score: float = Field(description="Confidence score between 0 and 1", default=0.5)
    reasoning: str = Field(description="Reasoning for the format", default="")



class WriterOutputType(BaseModel):
    """Writer output for thoughtful summary generation."""

    summary: str = Field(description="Thoughtful, comprehensive summary of the document")
    confidence_score: float = Field(description="Confidence score between 0 and 1", default=0.5)
    reasoning: str = Field(description="High-level reasoning behind the summary", default="")

# Resolve forward refs now that dependent classes are defined
CombinedMetadata.model_rebuild()
