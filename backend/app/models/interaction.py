from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    response_data = Column(JSON) # Concept, Steps, Final Answer
    feedback = Column(Boolean, nullable=True) # True for Up, False for Down
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content = Column(Text)
    # Vector column will be handled by pgvector in migrations
    created_at = Column(DateTime, default=datetime.utcnow)
