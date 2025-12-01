"""
Structured extraction models.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK


class DoorScheduleItem(BaseModel):
    """Single door entry from door schedule extraction."""
    mark: str = Field(..., description="Door mark/ID (e.g., D-101)")
    location: Optional[str] = Field(None, description="Room/area location")
    width_mm: Optional[int] = Field(None, description="Door width in mm")
    height_mm: Optional[int] = Field(None, description="Door height in mm")
    fire_rating: Optional[str] = Field(None, description="Fire rating (e.g., 1 HR)")
    material: Optional[str] = Field(None, description="Door material")
    frame_material: Optional[str] = Field(None, description="Frame material")
    hardware_set: Optional[str] = Field(None, description="Hardware set reference")
    remarks: Optional[str] = Field(None, description="Additional notes")
    page_number: int = Field(..., description="Source page number")
    file_name: str = Field(..., description="Source file name")


class WageScheduleItem(BaseModel):
    """Single wage entry from Davis-Bacon wage extraction."""
    classification: str = Field(..., description="Trade classification")
    rate_per_hour: Optional[float] = Field(None, description="Base hourly rate")
    fringe_per_hour: Optional[float] = Field(None, description="Fringe benefits per hour")
    total_per_hour: Optional[float] = Field(None, description="Total hourly compensation")
    notes: Optional[str] = Field(None, description="Additional notes/conditions")
    page_number: int = Field(..., description="Source page number")
    file_name: str = Field(..., description="Source file name")


class ExtractionResponse(BaseModel):
    """Response from structured extraction endpoint."""
    extraction_type: str = Field(..., description="Type of extraction (door_schedule, wage_schedule)")
    items: list[DoorScheduleItem | WageScheduleItem]
    total_items: int
    sources: list[dict] = Field(default_factory=list)
    processing_time_ms: float
    watermark: str = BUILD_WATERMARK
    project_context: str = PROJECT_CONTEXT_ID
