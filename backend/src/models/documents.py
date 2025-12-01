"""
Document models for PDF parsing and chunking.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


class PageContent(BaseModel):
    """Content from a single PDF page."""
    page_number: int
    text: str
    has_text: bool = True
    sheet_id: Optional[str] = None
    sheet_name: Optional[str] = None
    watermark: str = BUILD_WATERMARK


class DocumentMetadata(BaseModel):
    """Metadata for an ingested document."""
    file_name: str
    file_path: str
    page_count: int
    file_size_bytes: int
    ingested_at: datetime = Field(default_factory=datetime.now)
    project_id: str = "default_project"
    watermark: str = BUILD_WATERMARK
    project_context: str = PROJECT_CONTEXT_ID


class ParsedDocument(BaseModel):
    """Complete parsed document with pages."""
    metadata: DocumentMetadata
    pages: list[PageContent]
    watermark: str = BUILD_WATERMARK


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    chunk_id: str
    chunk_index: int
    file_name: str
    page_number: int
    section_title: Optional[str] = None
    sheet_id: Optional[str] = None
    text: str
    token_count: int
    start_char: int
    end_char: int
    created_at: datetime = Field(default_factory=datetime.now)
    watermark: str = BUILD_WATERMARK
    project_context: str = PROJECT_CONTEXT_ID

    def to_vector_payload(self) -> dict:
        """Convert to payload for vector storage."""
        return {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "file_name": self.file_name,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "sheet_id": self.sheet_id,
            "text": self.text,
            "token_count": self.token_count,
            "watermark": self.watermark,
            "project_context": self.project_context,
        }
