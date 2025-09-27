# run.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.config import load_config
load_config()

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
