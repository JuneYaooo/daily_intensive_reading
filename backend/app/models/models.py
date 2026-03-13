from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.db import Base

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(Enum("filter", "summary", "general"), default="general", nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FavoriteCard(Base):
    __tablename__ = "favorite_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source_url = Column(String(255))
    conclusion = Column(Text)
    key_points = Column(Text)  # Stored as JSON string
    quotes = Column(Text)      # Stored as JSON string
    author = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 