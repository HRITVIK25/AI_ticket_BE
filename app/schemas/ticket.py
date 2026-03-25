from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageNode(BaseModel):
    senderId: str
    senderRole: str
    message: str
    createdAt: datetime

class TicketCreate(BaseModel):
    title: str
    description: str

class TicketResponse(BaseModel):
    id: str
    org_id: str
    created_by: str
    assigned_to: Optional[str] = None
    title: str
    description: str
    status: str
    ai_response: Optional[str] = None
    messages: List[dict] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
