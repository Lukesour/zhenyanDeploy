#!/usr/bin/env python3
"""
生产环境后端服务启动脚本
用于 Fly.io 等生产环境部署
"""
import uvicorn
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("启动留学定位与选校规划系统后端服务 (生产环境)...")
    
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 4))
    
    print(f"服务地址: http://{host}:{port}")
    print(f"工作进程数: {workers}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        timeout_keep_alive=600,
        access_log=True
    )
