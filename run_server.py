import uvicorn
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # 启动FastAPI服务器
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["src"]
    )