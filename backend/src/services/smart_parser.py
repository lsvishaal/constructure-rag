"""
Smart PDF Parser - Structured Document Parsing

Treats PDFs as structured datasets, not blobs.
Extracts sheet metadata, handles image-only pages, preserves structure.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

import pdfplumber

from src.core.config import PROJECT_CONTEXT_ID

logger = logging.getLogger(__name__)

# Minimum characters to consider a page "has text"
MIN_TEXT_CHARS = 50


@dataclass
class SheetMetadata:
    """Structural metadata extracted from a sheet."""
    sheet_id: Optional[str] = None  # e.g., "AE501", "G-001"
    sheet_title: Optional[str] = None  # e.g., "DOOR SCHEDULE"
    discipline: Optional[str] = None  # e.g., "Architectural", "Electrical"
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    date: Optional[str] = None
    is_schedule_page: bool = False  # Door schedule, window schedule, etc.
    is_index_page: bool = False  # Sheet index
    document_type: str = "unknown"  # "drawings", "wage_determination", "specs"


@dataclass
class ParsedSheet:
    """A single parsed sheet/page with full metadata."""
    page_number: int
    file_name: str
    raw_text: str
    has_text: bool
    char_count: int
    metadata: SheetMetadata
    parse_error: bool = False
    error_message: Optional[str] = None
    watermark: str = PROJECT_CONTEXT_ID
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['metadata'] = asdict(self.metadata)
        return d


@dataclass 
class ParsedDocument:
    """Complete parsed document with all sheets."""
    file_name: str
    file_path: str
    total_pages: int
    text_pages: int
    image_only_pages: int
    parse_errors: int
    sheets: list[ParsedSheet]
    document_type: str
    project_id: Optional[str] = None
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    watermark: str = PROJECT_CONTEXT_ID
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "total_pages": self.total_pages,
            "text_pages": self.text_pages,
            "image_only_pages": self.image_only_pages,
            "parse_errors": self.parse_errors,
            "document_type": self.document_type,
            "project_id": self.project_id,
            "parsed_at": self.parsed_at,
            "watermark": self.watermark,
            "sheets": [s.to_dict() for s in self.sheets]
        }


class SmartPDFParser:
    """
    Smart PDF parser that treats documents as structured datasets.
    
    Features:
    - Extracts sheet-level metadata (sheet_id, title, discipline)
    - Handles image-only pages gracefully
    - Detects schedule pages for special handling
    - Per-page error handling (doesn't crash on bad pages)
    - Separates parsing from chunking
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    # Patterns for extracting construction drawing metadata
    SHEET_ID_PATTERNS = [
        r'\b([A-Z]{1,2}[-\s]?\d{3,4})\b',  # AE501, G-001, A-101
        r'\b(SHEET\s+[A-Z]?\d+)\b',  # SHEET A1
    ]
    
    SCHEDULE_KEYWORDS = [
        'door schedule', 'window schedule', 'finish schedule',
        'room schedule', 'equipment schedule', 'fixture schedule',
        'wage determination', 'wage rates', 'labor rates'
    ]
    
    INDEX_KEYWORDS = [
        'sheet index', 'drawing index', 'table of contents',
        'list of drawings', 'sheet list'
    ]
    
    DISCIPLINE_PATTERNS = {
        'A': 'Architectural',
        'S': 'Structural', 
        'M': 'Mechanical',
        'E': 'Electrical',
        'P': 'Plumbing',
        'C': 'Civil',
        'L': 'Landscape',
        'G': 'General',
        'AE': 'Architectural/Engineering',
    }

    def __init__(self, watermark: str = PROJECT_CONTEXT_ID):
        self.watermark = watermark
    
    def parse(self, pdf_path: str, project_id: Optional[str] = None) -> ParsedDocument:
        """
        Parse a PDF document into structured sheets.
        
        Args:
            pdf_path: Path to PDF file
            project_id: Optional project identifier
            
        Returns:
            ParsedDocument with all sheets and metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        file_name = pdf_path.name
        document_type = self._detect_document_type(file_name)
        
        logger.info(f"[{self.watermark}] Parsing {file_name} (type: {document_type})")
        
        sheets = []
        text_pages = 0
        image_only_pages = 0
        parse_errors = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                for idx, page in enumerate(pdf.pages, start=1):
                    sheet = self._parse_page(page, idx, file_name, document_type)
                    sheets.append(sheet)
                    
                    if sheet.parse_error:
                        parse_errors += 1
                    elif sheet.has_text:
                        text_pages += 1
                    else:
                        image_only_pages += 1
                    
                    # Log progress every 10 pages
                    if idx % 10 == 0 or idx == total_pages:
                        logger.info(f"[{self.watermark}] Parsed {idx}/{total_pages} pages")
                
        except Exception as e:
            logger.error(f"[{self.watermark}] Failed to open PDF {file_name}: {e}")
            raise ValueError(f"Invalid PDF: {e}")
        
        logger.info(
            f"[{self.watermark}] Completed {file_name}: "
            f"{total_pages} pages, {text_pages} with text, "
            f"{image_only_pages} image-only, {parse_errors} errors"
        )
        
        return ParsedDocument(
            file_name=file_name,
            file_path=str(pdf_path),
            total_pages=total_pages,
            text_pages=text_pages,
            image_only_pages=image_only_pages,
            parse_errors=parse_errors,
            sheets=sheets,
            document_type=document_type,
            project_id=project_id,
            watermark=self.watermark
        )
    
    def _parse_page(self, page, page_number: int, file_name: str, doc_type: str) -> ParsedSheet:
        """Parse a single page with error handling."""
        try:
            # Extract text
            raw_text = page.extract_text() or ""
            raw_text = self._normalize_text(raw_text)
            
            char_count = len(raw_text.strip())
            has_text = char_count >= MIN_TEXT_CHARS
            
            # Extract metadata
            metadata = self._extract_metadata(raw_text, page_number, doc_type)
            
            return ParsedSheet(
                page_number=page_number,
                file_name=file_name,
                raw_text=raw_text,
                has_text=has_text,
                char_count=char_count,
                metadata=metadata,
                watermark=self.watermark
            )
            
        except Exception as e:
            logger.warning(f"[{self.watermark}] Error parsing page {page_number}: {e}")
            return ParsedSheet(
                page_number=page_number,
                file_name=file_name,
                raw_text="",
                has_text=False,
                char_count=0,
                metadata=SheetMetadata(document_type=doc_type),
                parse_error=True,
                error_message=str(e),
                watermark=self.watermark
            )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace while preserving structure."""
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize line endings
        text = re.sub(r'\r\n?', '\n', text)
        # Collapse multiple newlines to max 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip control characters except newlines
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        return text.strip()
    
    def _extract_metadata(self, text: str, page_number: int, doc_type: str) -> SheetMetadata:
        """Extract structural metadata from page text."""
        text_lower = text.lower()
        
        metadata = SheetMetadata(document_type=doc_type)
        
        # Extract sheet ID
        for pattern in self.SHEET_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.sheet_id = match.group(1).upper().replace(' ', '')
                break
        
        # Determine discipline from sheet ID
        if metadata.sheet_id:
            for prefix, discipline in self.DISCIPLINE_PATTERNS.items():
                if metadata.sheet_id.startswith(prefix):
                    metadata.discipline = discipline
                    break
        
        # Check for schedule pages
        for keyword in self.SCHEDULE_KEYWORDS:
            if keyword in text_lower:
                metadata.is_schedule_page = True
                if not metadata.sheet_title:
                    # Try to extract title around the keyword
                    metadata.sheet_title = self._extract_title_near_keyword(text, keyword)
                break
        
        # Check for index pages
        for keyword in self.INDEX_KEYWORDS:
            if keyword in text_lower:
                metadata.is_index_page = True
                break
        
        # Extract project number (common patterns)
        project_patterns = [
            r'PROJECT\s*(?:NO\.?|NUMBER|#)?\s*[:\-]?\s*(\d{2,3}[-\s]?\d{2,3}[-\s]?\d{2,4})',
            r'(\d{3}-\d{2}-\d{3})',  # Pattern like 508-22-105
        ]
        for pattern in project_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.project_number = match.group(1).replace(' ', '')
                break
        
        return metadata
    
    def _extract_title_near_keyword(self, text: str, keyword: str) -> Optional[str]:
        """Extract title text near a keyword."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                # Return the line containing the keyword, cleaned up
                title = re.sub(r'\s+', ' ', line).strip()
                if len(title) > 5 and len(title) < 100:
                    return title.title()
        return None
    
    def _detect_document_type(self, file_name: str) -> str:
        """Detect document type from filename."""
        name_lower = file_name.lower()
        
        if 'drawing' in name_lower or 'plan' in name_lower:
            return 'drawings'
        elif 'wage' in name_lower or 'dba' in name_lower:
            return 'wage_determination'
        elif 'spec' in name_lower:
            return 'specifications'
        else:
            return 'unknown'
    
    def save_to_jsonl(self, document: ParsedDocument, output_path: str) -> str:
        """
        Save parsed document to JSONL format (one line per sheet).
        
        This separates parsing from indexing - allows re-chunking without reparsing.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write document metadata as first line
            doc_meta = {
                "type": "document_meta",
                "file_name": document.file_name,
                "total_pages": document.total_pages,
                "text_pages": document.text_pages,
                "image_only_pages": document.image_only_pages,
                "parse_errors": document.parse_errors,
                "document_type": document.document_type,
                "project_id": document.project_id,
                "parsed_at": document.parsed_at,
                "watermark": document.watermark
            }
            f.write(json.dumps(doc_meta) + '\n')
            
            # Write each sheet as a separate line
            for sheet in document.sheets:
                sheet_data = {
                    "type": "sheet",
                    **sheet.to_dict()
                }
                f.write(json.dumps(sheet_data) + '\n')
        
        logger.info(f"[{self.watermark}] Saved parsed data to {output_path}")
        return str(output_path)


# Convenience function
def parse_pdf(pdf_path: str, project_id: Optional[str] = None) -> ParsedDocument:
    """Parse a PDF file using the smart parser."""
    parser = SmartPDFParser()
    return parser.parse(pdf_path, project_id)
