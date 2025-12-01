"""
Chunking Service - Phase 1 (Optimized)

Splits text into overlapping chunks for RAG retrieval.
Includes structure-aware chunking to preserve tables and headers.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass, field
from typing import List, Optional
import re

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_index: int
    source_file: str
    page: int
    watermark: str = field(default=PROJECT_CONTEXT_ID)
    section: Optional[str] = None
    token_count: int = 0
    chunk_type: str = "text"  # 'text', 'table', 'header'


# =============================================================================
# Chunking Service
# =============================================================================

class ChunkingService:
    """
    Splits text into overlapping chunks for vector embedding.
    
    Features:
    - Structure-aware: Detects and preserves tables
    - Header injection: Prepends section headers to chunks
    - Smart overlap: Increases overlap for tables
    
    Watermark: Every chunk includes {BUILD_WATERMARK}
    """
    
    # Patterns for detecting structured content
    TABLE_PATTERNS = [
        r'\$\s*\d+\.\d{2}',           # Dollar amounts
        r'\d+\.\d+\s+\d+\.\d+',        # Multiple decimal numbers
        r'^\s*[A-Z\s]+\.+\s*\$',       # "TRADE...........$"
        r'Rates?\s+Fringes?',          # Wage table headers
    ]
    
    HEADER_PATTERNS = [
        r'^[A-Z][A-Z0-9\s\-]{5,}$',    # ALL CAPS HEADERS
        r'^SECTION\s+\d+',              # SECTION 123456
        r'^[A-Z]{2,4}\d{3,}',           # Code patterns like PLUM0072
    ]
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,       # Increased from 50 to 100
        watermark_id: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize chunking service.
        
        Args:
            chunk_size: Target number of words per chunk
            chunk_overlap: Number of overlapping words between chunks (20%)
            watermark_id: Project watermark to embed in chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.watermark_id = watermark_id
    
    def chunk(
        self,
        text: str,
        source_file: str,
        page: int,
        section: Optional[str] = None
    ) -> List[Chunk]:
        """
        Split text into overlapping chunks with structure awareness.
        
        Args:
            text: Text content to chunk
            source_file: Source PDF filename
            page: Page number in source document
            section: Optional section identifier
            
        Returns:
            List of Chunk objects with metadata and watermark
        """
        if not text or not text.strip():
            return []
        
        # Detect section header from text if not provided
        if not section:
            section = self._extract_section_header(text)
        
        # Check if this is tabular data - use special handling
        if self._is_tabular_data(text):
            return self._chunk_tabular(text, source_file, page, section)
        
        # Standard chunking for regular text
        return self._chunk_standard(text, source_file, page, section)
    
    def _chunk_standard(
        self,
        text: str,
        source_file: str,
        page: int,
        section: Optional[str]
    ) -> List[Chunk]:
        """Standard word-based chunking with overlap."""
        words = text.split()
        
        # If text is smaller than chunk size, return single chunk
        if len(words) <= self.chunk_size:
            chunk_text = text if not section else f"[{section}]\n{text}"
            return [
                Chunk(
                    text=chunk_text,
                    chunk_index=0,
                    source_file=source_file,
                    page=page,
                    section=section,
                    watermark=self.watermark_id,
                    token_count=len(words),
                    chunk_type="text",
                )
            ]
        
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            # Prepend section header to each chunk for context
            if section:
                chunk_text = f"[{section}]\n{chunk_text}"
            
            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    source_file=source_file,
                    page=page,
                    section=section,
                    watermark=self.watermark_id,
                    token_count=len(chunk_words),
                    chunk_type="text",
                )
            )
            
            chunk_index += 1
            # Move start forward, accounting for overlap
            start += self.chunk_size - self.chunk_overlap
            
            # Prevent infinite loop on last chunk
            if start >= len(words) - self.chunk_overlap:
                break
        
        return chunks
    
    def _chunk_tabular(
        self,
        text: str,
        source_file: str,
        page: int,
        section: Optional[str]
    ) -> List[Chunk]:
        """
        Special chunking for tabular data.
        
        Strategy:
        - Keep table rows together
        - Detect and preserve column headers
        - Prepend headers to each chunk
        """
        lines = text.split('\n')
        
        # Find potential header line (first line with multiple columns)
        header_line = None
        for line in lines[:5]:  # Check first 5 lines
            if self._looks_like_header(line):
                header_line = line.strip()
                break
        
        # Build chunks, keeping rows together
        chunks = []
        current_chunk_lines = []
        current_word_count = 0
        chunk_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_words = len(line.split())
            
            # If adding this line exceeds chunk size, save current chunk
            if current_word_count + line_words > self.chunk_size and current_chunk_lines:
                chunk_text = self._build_table_chunk(
                    current_chunk_lines, header_line, section
                )
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        source_file=source_file,
                        page=page,
                        section=section,
                        watermark=self.watermark_id,
                        token_count=current_word_count,
                        chunk_type="table",
                    )
                )
                chunk_index += 1
                current_chunk_lines = []
                current_word_count = 0
            
            current_chunk_lines.append(line)
            current_word_count += line_words
        
        # Don't forget the last chunk
        if current_chunk_lines:
            chunk_text = self._build_table_chunk(
                current_chunk_lines, header_line, section
            )
            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    source_file=source_file,
                    page=page,
                    section=section,
                    watermark=self.watermark_id,
                    token_count=current_word_count,
                    chunk_type="table",
                )
            )
        
        return chunks if chunks else self._chunk_standard(text, source_file, page, section)
    
    def _build_table_chunk(
        self,
        lines: List[str],
        header: Optional[str],
        section: Optional[str]
    ) -> str:
        """Build a table chunk with header prepended."""
        parts = []
        
        if section:
            parts.append(f"[{section}]")
        
        if header and header not in lines:
            parts.append(f"[TABLE HEADERS: {header}]")
        
        parts.extend(lines)
        
        return '\n'.join(parts)
    
    def _is_tabular_data(self, text: str) -> bool:
        """Detect if text contains tabular/structured data."""
        for pattern in self.TABLE_PATTERNS:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def _looks_like_header(self, line: str) -> bool:
        """Check if a line looks like a table header."""
        line = line.strip()
        if not line:
            return False
        
        # Check for common header keywords
        header_keywords = ['rate', 'fringe', 'classification', 'trade', 'mark', 'width', 'height']
        line_lower = line.lower()
        
        return sum(1 for kw in header_keywords if kw in line_lower) >= 2
    
    def _extract_section_header(self, text: str) -> Optional[str]:
        """Extract section header from the beginning of text."""
        lines = text.split('\n')[:3]  # Check first 3 lines
        
        for line in lines:
            line = line.strip()
            for pattern in self.HEADER_PATTERNS:
                if re.match(pattern, line):
                    return line[:100]  # Limit header length
        
        return None
