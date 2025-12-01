"""
PDF Parser Service - Phase 1

Extracts text and metadata from PDF documents.
Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

import pdfplumber

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ParsedPage:
    """Represents a single parsed page from a PDF."""
    page_number: int
    text: str
    watermark: str = field(default=PROJECT_CONTEXT_ID)
    
    
@dataclass
class ParsedDocument:
    """Represents a fully parsed PDF document."""
    filename: str
    page_count: int
    pages: List[ParsedPage]
    watermark: str = field(default=PROJECT_CONTEXT_ID)
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# PDF Parser
# =============================================================================

class PDFParser:
    """
    Parses PDF documents and extracts text content.
    
    Watermark: Every parsed document includes {BUILD_WATERMARK}
    """
    
    def __init__(self, watermark_id: str = PROJECT_CONTEXT_ID):
        self.watermark_id = watermark_id
    
    def parse(self, pdf_path: Path | str, max_pages: int | None = None, original_filename: str | None = None) -> ParsedDocument:
        """
        Parse a PDF file and extract text from all pages.
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Optional limit on number of pages to parse (for performance)
            original_filename: Original filename (used when parsing temp files)
            
        Returns:
            ParsedDocument with all pages and metadata
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        pdf_path = Path(pdf_path)
        
        # Check file exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Parse PDF
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                total_pages = len(pdf.pages)
                pages_to_parse = pdf.pages[:max_pages] if max_pages else pdf.pages
                
                for idx, page in enumerate(pages_to_parse, start=1):
                    text = page.extract_text() or ""
                    
                    parsed_page = ParsedPage(
                        page_number=idx,
                        text=text,
                        watermark=self.watermark_id,
                    )
                    pages.append(parsed_page)
                
                return ParsedDocument(
                    filename=original_filename or pdf_path.name,
                    page_count=total_pages,  # Always report total pages
                    pages=pages,
                    watermark=self.watermark_id,
                )
                
        except Exception as e:
            if "Invalid PDF" in str(e) or "EOF" in str(e) or "decrypt" in str(e).lower():
                raise ValueError(f"Invalid PDF: {e}")
            # Check if it's actually a PDF parsing error
            if "pdf" in str(e).lower() or not pdf_path.suffix.lower() == ".pdf":
                raise ValueError(f"Invalid PDF: {e}")
            raise ValueError(f"Invalid PDF: {e}")
