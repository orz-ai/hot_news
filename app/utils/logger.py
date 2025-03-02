import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import pytz
from datetime import datetime

from app.core.config import get_logging_config

# 获取日志配置
log_config = get_logging_config()

# 确保日志目录存在
os.makedirs(log_config.dir, exist_ok=True)

# 自定义日志格式化器，使用配置的时区
class CustomFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        tz = pytz.timezone(log_config.timezone)
        return dt.replace(tzinfo=pytz.utc).astimezone(tz)
    
    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

# 创建日志记录器
log = logging.getLogger('app')
log.setLevel(getattr(logging, log_config.level))

# 清除现有处理器
for handler in log.handlers[:]:
    log.removeHandler(handler)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, log_config.level))
console_formatter = CustomFormatter(log_config.format)
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)

# 创建文件处理器 - 按大小轮转
file_handler = RotatingFileHandler(
    os.path.join(log_config.dir, log_config.file), 
    maxBytes=log_config.max_size, 
    backupCount=log_config.backup_count,
    encoding='utf-8'
)
file_handler.setLevel(getattr(logging, log_config.level))
file_formatter = CustomFormatter(log_config.format)
file_handler.setFormatter(file_formatter)
log.addHandler(file_handler)

# 创建文件处理器 - 按日期轮转
daily_handler = TimedRotatingFileHandler(
    os.path.join(log_config.dir, 'app.daily.log'),
    when='midnight',
    interval=1,
    backupCount=log_config.daily_backup_count,
    encoding='utf-8'
)
daily_handler.setLevel(getattr(logging, log_config.level))
daily_handler.setFormatter(file_formatter)
log.addHandler(daily_handler)

# 防止日志传播到父记录器
log.propagate = False

# 记录启动信息
log.info(f"Logger initialized at {datetime.now(pytz.timezone(log_config.timezone)).strftime('%Y-%m-%d %H:%M:%S')}")