import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime
from config.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    # Clerk org ID (PRIMARY KEY)
    id = Column(String, primary_key=True)  

    # Optional human-readable fields
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    executive_id = Column(String, nullable=True)

    # Status control (VERY useful)
    is_active = Column(Boolean, default=True)

    # Metadata / future flexibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    created_by = Column(String, nullable=False)  # customer ID
    assigned_to = Column(String, nullable=True)  # executive ID

    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    status = Column(String, default="CREATED")

    ai_response = Column(String, nullable=True)

    # Stores list of message objects: senderId, senderRole, message, createdAt
    messages = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)