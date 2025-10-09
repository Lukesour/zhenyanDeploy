#!/usr/bin/env python3
"""
简化的后端服务启动脚本
"""
import uvicorn
from pathlib import Path
import sys
import os

# 添加当前目录到Python路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

if __name__ == "__main__":
    print("启动留学定位与选校规划系统后端服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        timeout_keep_alive=600
    )

