from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from config.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    # Clerk org ID (PRIMARY KEY)
    id = Column(String, primary_key=True)  

    # Optional human-readable fields
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Status control (VERY useful)
    is_active = Column(Boolean, default=True)

    # Metadata / future flexibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)