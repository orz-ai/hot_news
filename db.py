from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://root:123456@localhost/news_crawler?charset=utf8mb4')
Base = declarative_base()


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


Session = sessionmaker(bind=engine)
session = Session()


def insert_news(news_list):
    session.add_all(news_list)
    session.commit()
    session.close()
