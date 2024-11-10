from sqlalchemy import Column, String, Integer, DateTime

from app.core import db
from app.core.db import Base


class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    score = Column(String)
    desc = Column(String)
    source = Column(String)
    create_time = Column(DateTime)
    update_time = Column(DateTime)

    # to json
    def to_cache_json(self):
        return {
            "title": self.title,
            "url": self.url,
            "score": self.score,
            "desc": self.desc,
        }


def insert_news(news_list):
    db.insert_news(news_list)
