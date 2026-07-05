"""
models.py

Pydantic schemas for API requests and responses.
Kept separate from database.py so the API contract can evolve
independently of the storage schema.
"""

from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: int
    filename: str
    image_path: str
    timestamp: str
    processed: bool


class RecordResponse(BaseModel):
    id: int
    filename: str
    original_filename: Optional[str] = None
    image_path: str
    timestamp: str
    brightness: Optional[float] = None
    blur: Optional[float] = None
    output: Optional[str] = None
    processed: bool
    camera_id: Optional[str] = None
    location: Optional[str] = None


class HistoryResponse(BaseModel):
    total: int
    records: list[RecordResponse]


class MessageResponse(BaseModel):
    message: str
