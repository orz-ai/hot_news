import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
import pytz

from app.utils.logger import log
from app.core.config import get_notification_config


class DingTalkNotifier:
    """钉钉机器人通知器"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.webhook_url = self.config.get('dingtalk', {}).get('webhook_url', '')
        self.secret = self.config.get('dingtalk', {}).get('secret', '')
        self.enabled = self.config.get('dingtalk', {}).get('enabled', False)
        self.timeout = self.config.get('dingtalk', {}).get('timeout', 10)
        self.shanghai_tz = pytz.timezone('Asia/Shanghai')
        
        if not self.webhook_url and self.enabled:
            log.warning("DingTalk webhook URL not configured, notifications will be disabled")
            self.enabled = False
    
    def _generate_sign(self, timestamp: int) -> str:
        """生成钉钉机器人签名"""
        if not self.secret:
            return ""
        
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到钉钉"""
        if not self.enabled:
            log.debug("DingTalk notifications are disabled")
            return False
        
        try:
            # 生成时间戳和签名
            timestamp = int(round(time.time() * 1000))
            sign = self._generate_sign(timestamp)
            
            # 构建请求URL
            url = self.webhook_url
            if sign:
                url += f"&timestamp={timestamp}&sign={sign}"
            
            # 发送请求
            response = requests.post(
                url,
                json=message,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    log.info("DingTalk notification sent successfully")
                    return True
                else:
                    log.error(f"DingTalk API error: {result.get('errmsg', 'Unknown error')}")
                    return False
            else:
                log.error(f"DingTalk HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"Failed to send DingTalk notification: {str(e)}")
            return False
    
    def send_text_message(self, content: str, at_mobiles: Optional[List[str]] = None, 
                         at_all: bool = False) -> bool:
        """发送文本消息"""
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        if at_mobiles or at_all:
            message["at"] = {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        
        return self._send_message(message)
    
    def send_markdown_message(self, title: str, text: str, 
                            at_mobiles: Optional[List[str]] = None, 
                            at_all: bool = False) -> bool:
        """发送Markdown消息"""
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }
        
        if at_mobiles or at_all:
            message["at"] = {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        
        return self._send_message(message)
    
    def send_crawler_error(self, crawler_name: str, error_msg: str, 
                          date_str: str, is_retry: bool = False) -> bool:
        """发送爬虫错误通知"""
        current_time = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        retry_text = "重试失败" if is_retry else "首次失败"
        
        title = f"🚨 爬虫异常通知 - {crawler_name}"
        content = f"""
## {title}

**时间**: {current_time}\n
**爬虫**: {crawler_name}\n
**日期**: {date_str}\n
**状态**: {retry_text}\n
**错误信息**: 
```
{error_msg}
```

请及时检查爬虫状态！
        """.strip()
        
        return self.send_markdown_message(title, content)
    
    def send_crawler_timeout(self, timeout_seconds: int) -> bool:
        """发送爬虫超时通知"""
        current_time = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        title = "⏰ 爬虫超时通知"
        content = f"""
## {title}

**时间**: {current_time}\n
**超时时长**: {timeout_seconds}秒\n
**状态**: 爬虫任务执行超时被强制终止

请检查爬虫性能或调整超时配置！
        """.strip()
        
        return self.send_markdown_message(title, content)
    
    def send_crawler_summary(self, success_count: int, total_count: int, 
                           failed_crawlers: List[str], duration: float, 
                           date_str: str) -> bool:
        """发送爬虫执行摘要通知（仅在有失败时发送）"""
        if success_count == total_count:
            # 全部成功，不发送通知
            return True
        
        current_time = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建失败爬虫列表
        failed_list = "\n".join([f"- {name}" for name in failed_crawlers])
        
        title = f"📊 爬虫执行摘要 - {date_str}"
        content = f"""
## {title}

**时间**: {current_time}\n
**日期**: {date_str}\n
**执行时长**: {duration:.2f}秒\n
**成功**: {success_count}/{total_count}\n
**失败**: {len(failed_crawlers)}

**失败的爬虫**:
{failed_list}

请关注失败的爬虫状态！
        """.strip()
        
        return self.send_markdown_message(title, content)
    
    def send_analysis_error(self, error_msg: str, date_str: str) -> bool:
        """发送数据分析错误通知"""
        current_time = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        title = "🔍 数据分析异常通知"
        content = f"""
## {title}

**时间**: {current_time}\n
**日期**: {date_str}\n
**错误信息**: 
```
{error_msg}
```

数据分析任务执行失败，请检查分析模块！
        """.strip()
        
        return self.send_markdown_message(title, content)


class NotificationManager:
    """通知管理器，支持多种通知方式"""
    
    def __init__(self):
        self.dingtalk = DingTalkNotifier()
        # 可以在这里添加其他通知方式，如企业微信、邮件等
    
    def notify_crawler_error(self, crawler_name: str, error_msg: str, 
                           date_str: str, is_retry: bool = False):
        """通知爬虫错误"""
        self.dingtalk.send_crawler_error(crawler_name, error_msg, date_str, is_retry)
    
    def notify_crawler_timeout(self, timeout_seconds: int):
        """通知爬虫超时"""
        self.dingtalk.send_crawler_timeout(timeout_seconds)
    
    def notify_crawler_summary(self, success_count: int, total_count: int, 
                             failed_crawlers: List[str], duration: float, 
                             date_str: str):
        """通知爬虫执行摘要"""
        self.dingtalk.send_crawler_summary(success_count, total_count, 
                                         failed_crawlers, duration, date_str)
    
    def notify_analysis_error(self, error_msg: str, date_str: str):
        """通知数据分析错误"""
        self.dingtalk.send_analysis_error(error_msg, date_str)


# 全局通知管理器实例
notification_manager = NotificationManager()