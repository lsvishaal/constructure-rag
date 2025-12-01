"""
Chat models for RAG Q&A.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


class Source(BaseModel):
    """Citation source for an answer."""
    file_name: str
    page_number: int
    section_title: Optional[str] = None
    snippet: str = Field(..., max_length=500)
    relevance_score: float = 0.0


class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: list[Source] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request to the chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    mode: Literal["qa", "extraction", "sources_only"] = "qa"


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    answer: str
    sources: list[Source]
    conversation_id: str
    mode: str
    processing_time_ms: float
    chunks_retrieved: int
    watermark: str = BUILD_WATERMARK
    project_context: str = PROJECT_CONTEXT_ID
    
    # Optional structured data (for extraction mode)
    structured_data: Optional[dict | list] = None
