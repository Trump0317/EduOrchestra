import sys
from pathlib import Path

# 确保 server/ 在 Python 路径中，以便 from main import app 生效
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
