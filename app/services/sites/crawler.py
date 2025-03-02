from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Crawler(ABC):
    """爬虫基类"""
    
    def __init__(self):
        self.header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/86.0.4240.183 Safari/537.36"
        }
        self.timeout = 10
    
    @abstractmethod
    def fetch(self, date_str: str) -> List[Dict[str, Any]]:
        """获取新闻列表"""
        pass
    
    @abstractmethod
    def crawler_name(self) -> str:
        """获取爬虫名称"""
        pass
