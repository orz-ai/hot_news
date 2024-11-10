from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://root:123456@localhost/news_crawler?charset=utf8mb4')
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


def insert_news(model):
    session.add_all(model)
    session.commit()
    session.close()
