import sys
import os
# 把当前目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入应用
from app.app import app

if __name__ == "__main__":
    app.run() 