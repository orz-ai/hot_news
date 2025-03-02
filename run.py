# run.py
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 加载配置
from app.core.config import load_config
load_config()

# 导入应用
from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_app_config
    
    app_config = get_app_config()
    uvicorn.run(
        "app.main:app", 
        host=app_config.host, 
        port=app_config.port, 
        reload=app_config.debug
    )
