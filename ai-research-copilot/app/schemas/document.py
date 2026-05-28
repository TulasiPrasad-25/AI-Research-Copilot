from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size: Optional[int]
    status: DocumentStatus
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    total: int
    items: list[DocumentOut]
