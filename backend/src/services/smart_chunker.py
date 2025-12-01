"""
Smart Chunker - Structure-Preserving Text Chunking

Chunks per page/sheet, preserves metadata, handles schedules specially.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.config import PROJECT_CONTEXT_ID
from src.services.smart_parser import ParsedSheet, ParsedDocument

logger = logging.getLogger(__name__)

# Minimum tokens to keep a chunk (skip noise)
MIN_CHUNK_TOKENS = 30


@dataclass
class SmartChunk:
    """A chunk with full metadata for RAG retrieval."""
    text: str
    chunk_index: int
    
    # Source tracking (for citations)
    file_name: str
    page_number: int
    sheet_id: Optional[str] = None
    sheet_title: Optional[str] = None
    
    # Classification
    document_type: str = "unknown"
    discipline: Optional[str] = None
    is_schedule_chunk: bool = False
    
    # Project context
    project_id: Optional[str] = None
    
    # Token estimate
    token_count: int = 0
    
    watermark: str = PROJECT_CONTEXT_ID
    
    def to_metadata_dict(self) -> dict:
        """Return metadata dict for vector store."""
        return {
            "file_name": self.file_name,
            "page_number": self.page_number,
            "sheet_id": self.sheet_id,
            "sheet_title": self.sheet_title,
            "document_type": self.document_type,
            "discipline": self.discipline,
            "is_schedule_chunk": self.is_schedule_chunk,
            "project_id": self.project_id,
            "chunk_index": self.chunk_index,
            "watermark": self.watermark
        }


class SmartChunker:
    """
    Structure-preserving chunker for construction documents.
    
    Key principles:
    - Chunk PER PAGE, not across pages (preserves citations)
    - Keep schedule rows together when possible
    - Skip chunks below minimum token threshold
    - Store rich metadata for retrieval filtering
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    def __init__(
        self,
        chunk_size: int = 400,  # target tokens per chunk
        chunk_overlap: int = 50,  # overlap tokens
        min_chunk_tokens: int = MIN_CHUNK_TOKENS,
        watermark: str = PROJECT_CONTEXT_ID
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_tokens = min_chunk_tokens
        self.watermark = watermark
    
    def chunk_document(self, document: ParsedDocument) -> list[SmartChunk]:
        """
        Chunk an entire parsed document.
        
        Returns list of SmartChunk objects with full metadata.
        """
        all_chunks = []
        chunk_index = 0
        
        for sheet in document.sheets:
            # Skip pages with parse errors or no text
            if sheet.parse_error or not sheet.has_text:
                logger.debug(
                    f"[{self.watermark}] Skipping page {sheet.page_number}: "
                    f"error={sheet.parse_error}, has_text={sheet.has_text}"
                )
                continue
            
            # Chunk this sheet
            sheet_chunks = self._chunk_sheet(sheet, document.project_id, chunk_index)
            all_chunks.extend(sheet_chunks)
            chunk_index += len(sheet_chunks)
        
        logger.info(
            f"[{self.watermark}] Created {len(all_chunks)} chunks from "
            f"{document.file_name} ({document.text_pages} text pages)"
        )
        
        return all_chunks
    
    def _chunk_sheet(
        self, 
        sheet: ParsedSheet, 
        project_id: Optional[str],
        start_index: int
    ) -> list[SmartChunk]:
        """Chunk a single sheet, respecting structure."""
        text = sheet.raw_text
        
        # For schedule pages, try to keep logical rows together
        if sheet.metadata.is_schedule_page:
            return self._chunk_schedule_page(sheet, project_id, start_index)
        
        # Standard chunking with word-based windows
        return self._chunk_text(sheet, project_id, start_index)
    
    def _chunk_text(
        self,
        sheet: ParsedSheet,
        project_id: Optional[str],
        start_index: int
    ) -> list[SmartChunk]:
        """Standard word-based chunking with overlap."""
        text = sheet.raw_text
        words = text.split()
        
        if len(words) < self.min_chunk_tokens:
            # Text too short - either skip or keep as single chunk
            if len(words) < 10:
                return []
            
            # Keep as single chunk
            return [self._create_chunk(
                text=text,
                sheet=sheet,
                project_id=project_id,
                chunk_index=start_index,
                token_count=len(words)
            )]
        
        chunks = []
        chunk_idx = start_index
        pos = 0
        
        while pos < len(words):
            end = min(pos + self.chunk_size, len(words))
            chunk_words = words[pos:end]
            chunk_text = ' '.join(chunk_words)
            
            # Skip if below minimum
            if len(chunk_words) >= self.min_chunk_tokens:
                chunks.append(self._create_chunk(
                    text=chunk_text,
                    sheet=sheet,
                    project_id=project_id,
                    chunk_index=chunk_idx,
                    token_count=len(chunk_words)
                ))
                chunk_idx += 1
            
            # Move forward with overlap
            pos += self.chunk_size - self.chunk_overlap
            
            # Avoid infinite loop
            if pos >= end:
                break
        
        return chunks
    
    def _chunk_schedule_page(
        self,
        sheet: ParsedSheet,
        project_id: Optional[str],
        start_index: int
    ) -> list[SmartChunk]:
        """
        Special chunking for schedule pages.
        
        Tries to keep table rows together rather than splitting mid-row.
        """
        text = sheet.raw_text
        lines = text.split('\n')
        
        chunks = []
        chunk_idx = start_index
        current_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = len(line.split())
            
            # If adding this line exceeds chunk size, flush current chunk
            if current_tokens + line_tokens > self.chunk_size and current_lines:
                chunk_text = '\n'.join(current_lines)
                if current_tokens >= self.min_chunk_tokens:
                    chunks.append(self._create_chunk(
                        text=chunk_text,
                        sheet=sheet,
                        project_id=project_id,
                        chunk_index=chunk_idx,
                        token_count=current_tokens,
                        is_schedule=True
                    ))
                    chunk_idx += 1
                current_lines = []
                current_tokens = 0
            
            current_lines.append(line)
            current_tokens += line_tokens
        
        # Flush remaining
        if current_lines and current_tokens >= self.min_chunk_tokens:
            chunk_text = '\n'.join(current_lines)
            chunks.append(self._create_chunk(
                text=chunk_text,
                sheet=sheet,
                project_id=project_id,
                chunk_index=chunk_idx,
                token_count=current_tokens,
                is_schedule=True
            ))
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        sheet: ParsedSheet,
        project_id: Optional[str],
        chunk_index: int,
        token_count: int,
        is_schedule: bool = False
    ) -> SmartChunk:
        """Create a SmartChunk with full metadata."""
        return SmartChunk(
            text=text,
            chunk_index=chunk_index,
            file_name=sheet.file_name,
            page_number=sheet.page_number,
            sheet_id=sheet.metadata.sheet_id,
            sheet_title=sheet.metadata.sheet_title,
            document_type=sheet.metadata.document_type,
            discipline=sheet.metadata.discipline,
            is_schedule_chunk=is_schedule or sheet.metadata.is_schedule_page,
            project_id=project_id,
            token_count=token_count,
            watermark=self.watermark
        )


# Convenience function
def chunk_document(document: ParsedDocument, chunk_size: int = 400) -> list[SmartChunk]:
    """Chunk a parsed document using smart chunker."""
    chunker = SmartChunker(chunk_size=chunk_size)
    return chunker.chunk_document(document)
