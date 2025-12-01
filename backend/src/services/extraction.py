"""
Structured Extraction Service - Phase 5

Extract structured data (tables, schedules) from construction documents.
Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass, field
from typing import Any
import re
import logging

from src.core.config import PROJECT_CONTEXT_ID
from src.services.retrieval import RetrievalService, RetrievalResult

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class DoorScheduleEntry:
    """
    A single door schedule entry.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    door_id: str
    room: str | None = None
    width: str | None = None
    height: str | None = None
    material: str | None = None
    fire_rating: str | None = None
    hardware: str | None = None
    notes: str | None = None
    watermark: str = PROJECT_CONTEXT_ID


@dataclass
class ExtractedTable:
    """
    Generic extracted table data.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    headers: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    watermark: str = PROJECT_CONTEXT_ID


@dataclass
class SourceReference:
    """
    Reference to source document.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    source_file: str
    page: int | None
    text_snippet: str
    watermark: str = PROJECT_CONTEXT_ID


@dataclass
class ExtractedData:
    """
    Complete extraction result with data and sources.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    data_type: str
    entries: list[Any] = field(default_factory=list)
    sources: list[SourceReference] = field(default_factory=list)
    raw_text: str = ""
    error: bool = False
    error_message: str | None = None
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# Extraction Service
# =============================================================================

class ExtractionService:
    """
    Service for extracting structured data from construction documents.
    
    Supports:
    - Door schedules
    - Window schedules
    - Generic tables
    - Specification data
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    EXTRACTION_PROMPT = """Extract structured data from the following construction document text.
Return the data in a structured format.

Data Type: {data_type}
Source Text:
{context}

---
Extract the requested information and format it as structured data.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025"""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: str = "mock",
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize extraction service.
        
        Args:
            retrieval_service: Service for retrieving relevant documents
            llm_provider: LLM provider ('mock', 'ollama', 'openai')
            watermark: Project watermark identifier
        """
        self.retrieval_service = retrieval_service
        self.llm_provider = llm_provider
        self.watermark = watermark
        
        logger.info(f"[{self.watermark}] ExtractionService initialized")
    
    def extract(
        self,
        query: str,
        data_type: str,
        top_k: int = 10
    ) -> ExtractedData:
        """
        Extract structured data based on query.
        
        Args:
            query: Query describing what to extract
            data_type: Type of data ('door_schedule', 'window_schedule', 'table')
            top_k: Number of relevant documents to retrieve
            
        Returns:
            ExtractedData with structured entries and sources
        """
        try:
            # Retrieve relevant documents
            results = self.retrieval_service.retrieve(query, top_k=top_k)
            
            if not results:
                return ExtractedData(
                    data_type=data_type,
                    entries=[],
                    sources=[],
                    error=False,
                    watermark=self.watermark
                )
            
            # Build sources
            sources = self._build_sources(results)
            
            # Extract based on data type
            if data_type == "door_schedule":
                entries = self._extract_door_schedule(results)
            elif data_type == "window_schedule":
                entries = self._extract_window_schedule(results)
            elif data_type == "table":
                entries = self._extract_generic_table(results)
            else:
                entries = self._extract_generic(results)
            
            # Combine all text
            raw_text = "\n".join(r.text for r in results)
            
            return ExtractedData(
                data_type=data_type,
                entries=entries,
                sources=sources,
                raw_text=raw_text,
                error=False,
                watermark=self.watermark
            )
            
        except Exception as e:
            logger.error(f"[{self.watermark}] Extraction error: {e}")
            return ExtractedData(
                data_type=data_type,
                entries=[],
                sources=[],
                error=True,
                error_message=str(e),
                watermark=self.watermark
            )
    
    def _build_sources(self, results: list[RetrievalResult]) -> list[SourceReference]:
        """Build source references from retrieval results."""
        sources = []
        for result in results:
            sources.append(SourceReference(
                source_file=result.metadata.get("source_file", "unknown"),
                page=result.metadata.get("page"),
                text_snippet=result.text[:100] + "..." if len(result.text) > 100 else result.text,
                watermark=self.watermark
            ))
        return sources
    
    def _extract_door_schedule(self, results: list[RetrievalResult]) -> list[DoorScheduleEntry]:
        """Extract door schedule entries from results."""
        entries = []
        
        for result in results:
            text = result.text
            
            # Try to parse door schedule format
            # Example: "Door D-101, Width 36", Height 84", Material Hollow Metal"
            door_matches = re.findall(
                r'Door\s+([A-Z]?-?\d+)[,:]?\s*'
                r'(?:Width\s+(\d+)"?)?\s*'
                r'(?:Height\s+(\d+)"?)?\s*'
                r'(?:Material\s+([\w\s]+?))?'
                r'(?:,\s*Fire Rating\s+([\w\s]+))?',
                text,
                re.IGNORECASE
            )
            
            for match in door_matches:
                door_id, width, height, material, fire_rating = match
                entries.append(DoorScheduleEntry(
                    door_id=door_id.strip() if door_id else "Unknown",
                    width=f'{width}"' if width else None,
                    height=f'{height}"' if height else None,
                    material=material.strip() if material else None,
                    fire_rating=fire_rating.strip() if fire_rating else None,
                    watermark=self.watermark
                ))
            
            # If no regex match, create entry from text
            if not door_matches and "door" in text.lower():
                entries.append(DoorScheduleEntry(
                    door_id="Extracted",
                    notes=text[:200],
                    watermark=self.watermark
                ))
        
        return entries
    
    def _extract_window_schedule(self, results: list[RetrievalResult]) -> list[dict]:
        """Extract window schedule entries from results."""
        entries = []
        
        for result in results:
            text = result.text
            
            # Parse window format
            window_matches = re.findall(
                r'([WS]?-?\d+)[,:]?\s*'
                r'(?:Size\s+([\d"x]+))?\s*'
                r'(?:Type\s+([\w\s]+?))?'
                r'(?:,\s*Glass\s+([\w\s]+))?',
                text,
                re.IGNORECASE
            )
            
            for match in window_matches:
                window_id, size, window_type, glass = match
                entries.append({
                    "window_id": window_id.strip() if window_id else "Unknown",
                    "size": size if size else None,
                    "type": window_type.strip() if window_type else None,
                    "glass": glass.strip() if glass else None,
                    "watermark": self.watermark
                })
            
            if not window_matches and "window" in text.lower():
                entries.append({
                    "window_id": "Extracted",
                    "raw_text": text[:200],
                    "watermark": self.watermark
                })
        
        return entries
    
    def _extract_generic_table(self, results: list[RetrievalResult]) -> list[dict]:
        """Extract generic table data from results."""
        entries = []
        
        for result in results:
            entries.append({
                "text": result.text,
                "source": result.metadata.get("source_file"),
                "page": result.metadata.get("page"),
                "watermark": self.watermark
            })
        
        return entries
    
    def _extract_generic(self, results: list[RetrievalResult]) -> list[dict]:
        """Generic extraction for unknown data types."""
        return self._extract_generic_table(results)
