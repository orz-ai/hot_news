from datetime import datetime
from typing import Optional, List, Dict, Any
from .models import Base, News

# 移除对 SQLAlchemy 的依赖
# from app.core.db import Base

# 定义一个简单的数据类来替代 SQLAlchemy 模型
class News:
    """新闻数据模型"""
    
    def __init__(self, 
                 title: str = "", 
                 content: str = "", 
                 url: str = "", 
                 source: str = "", 
                 publish_time: Optional[datetime] = None):
        self.id: Optional[int] = None
        self.title = title
        self.content = content
        self.url = url
        self.source = source
        self.publish_time = publish_time or datetime.now()
        self.created_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'News':
        """从字典创建新闻对象"""
        news = cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            url=data.get('url', ''),
            source=data.get('source', ''),
            publish_time=data.get('publish_time')
        )
        if 'id' in data:
            news.id = data['id']
        if 'created_at' in data:
            news.created_at = data['created_at']
        return news
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'publish_time': self.publish_time,
            'created_at': self.created_at
        }

def insert_news(news_list):
    """将新闻列表插入数据库"""
    from app.core import db
    # 如果传入的是 News 对象列表，转换为字典列表
    if news_list and isinstance(news_list[0], News):
        news_list = [news.to_dict() for news in news_list]
    return db.insert_news(news_list)
