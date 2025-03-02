from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(255), nullable=False, unique=True)
    source = Column(String(50), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False) 