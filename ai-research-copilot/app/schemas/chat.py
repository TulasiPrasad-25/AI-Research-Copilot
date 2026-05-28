from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatSessionCreate(BaseModel):
    title: str = "New Chat"


class ChatSessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageIn(BaseModel):
    question: str
    session_id: int


class SourceChunk(BaseModel):
    content: str
    document_title: str
    page: Optional[int] = None


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[list[SourceChunk]] = None
    created_at: datetime

    class Config:
        from_attributes = True
