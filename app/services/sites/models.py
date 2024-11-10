import datetime

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DailyNews(Base):
    __tablename__ = 'tab_daily_news'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    desc = Column(String(255))
    link = Column(String(255))
    type = Column(Integer, default=0)
    score = Column(Integer, default=0)
    times = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.datetime.now)
    update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
