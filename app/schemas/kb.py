from pydantic import BaseModel
from typing import List,Optional
from datetime import datetime
from uuid import UUID


class KBIngestResponse(BaseModel):
    message: str
    kb_id: str


class KBResponse(BaseModel):
    id: UUID
    org_id: str
    title: str
    description: Optional[str] = None
    file_names: List[str] = []
    tag: Optional[str] = None
    type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KBSearchResult(BaseModel):
    id: str
    org_id: str
    title: str
    kb_id: str
    description: Optional[str] = None
    file_names: List[str] = []
    tag: Optional[str] = None
    content: str
    type: str
    score: float          # cosine similarity score
    created_at: datetime
