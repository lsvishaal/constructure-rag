"""
Fast PDF Parser using PyMuPDF (fitz).

Speed: ~30 pages/second (vs 0.3 with pdfplumber on complex PDFs)

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import fitz  # PyMuPDF

from src.core.config import PROJECT_CONTEXT_ID

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """Single parsed page."""
    page_number: int
    file_name: str
    text: str
    has_text: bool
    char_count: int
    sheet_id: str | None = None


@dataclass
class ParseProgress:
    """Progress during parsing."""
    current_page: int
    total_pages: int
    text_pages: int
    image_pages: int
    elapsed_seconds: float
    pages_per_second: float
    status: str = "parsing"
    
    @property
    def percent(self) -> float:
        return (self.current_page / self.total_pages * 100) if self.total_pages > 0 else 0


@dataclass
class ParseResult:
    """Complete parsing result."""
    file_name: str
    pages: list[ParsedPage]
    total_pages: int
    text_pages: int
    image_pages: int
    elapsed_seconds: float
    pages_per_second: float
    watermark: str = PROJECT_CONTEXT_ID


class FastPDFParser:
    """
    Lightning-fast PDF parser using PyMuPDF.
    
    68 pages in ~2.5 seconds (vs 4+ minutes with pdfplumber).
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    MIN_TEXT_CHARS = 50
    
    def __init__(self, project_id: str = PROJECT_CONTEXT_ID):
        self.project_id = project_id
    
    def parse(
        self,
        pdf_path: str,
        on_progress: Callable[[ParseProgress], None] | None = None,
    ) -> ParseResult:
        """
        Parse PDF and return all pages with progress updates.
        
        Args:
            pdf_path: Path to PDF file
            on_progress: Optional callback for progress updates
            
        Returns:
            ParseResult with all pages and stats
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        file_name = pdf_path.name
        start_time = time.time()
        
        pages = []
        text_pages = 0
        image_pages = 0
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            logger.info(f"[{self.project_id}] 📄 Parsing {file_name} ({total_pages} pages)")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text().strip()
                
                has_text = len(text) > self.MIN_TEXT_CHARS
                
                if has_text:
                    text_pages += 1
                    sheet_id = self._extract_sheet_id(text)
                else:
                    image_pages += 1
                    sheet_id = None
                
                pages.append(ParsedPage(
                    page_number=page_num + 1,
                    file_name=file_name,
                    text=text,
                    has_text=has_text,
                    char_count=len(text),
                    sheet_id=sheet_id,
                ))
                
                # Progress callback
                if on_progress:
                    elapsed = time.time() - start_time
                    on_progress(ParseProgress(
                        current_page=page_num + 1,
                        total_pages=total_pages,
                        text_pages=text_pages,
                        image_pages=image_pages,
                        elapsed_seconds=elapsed,
                        pages_per_second=(page_num + 1) / elapsed if elapsed > 0 else 0,
                    ))
            
            doc.close()
            
        except Exception as e:
            logger.error(f"[{self.project_id}] ❌ Error parsing {file_name}: {e}")
            raise
        
        elapsed = time.time() - start_time
        pps = total_pages / elapsed if elapsed > 0 else 0
        
        # Final progress
        if on_progress:
            on_progress(ParseProgress(
                current_page=total_pages,
                total_pages=total_pages,
                text_pages=text_pages,
                image_pages=image_pages,
                elapsed_seconds=elapsed,
                pages_per_second=pps,
                status="complete",
            ))
        
        logger.info(
            f"[{self.project_id}] ✅ Parsed {file_name}: "
            f"{text_pages}/{total_pages} text pages in {elapsed:.1f}s ({pps:.0f} pg/s)"
        )
        
        return ParseResult(
            file_name=file_name,
            pages=pages,
            total_pages=total_pages,
            text_pages=text_pages,
            image_pages=image_pages,
            elapsed_seconds=elapsed,
            pages_per_second=pps,
        )
    
    def _extract_sheet_id(self, text: str) -> str | None:
        """Extract sheet ID from text."""
        patterns = [
            r'\b([A-Z]{1,2}\d{1,2}\.\d{1,2})\b',  # A1.01
            r'\b([A-Z]{1,3}-?\d{1,3})\b',  # M-101
        ]
        
        search_text = text[:1000]
        for pattern in patterns:
            match = re.search(pattern, search_text)
            if match:
                return match.group(1)
        return None
