"""测试环境变量：在导入 app 前设置。"""

from __future__ import annotations

import os
from pathlib import Path

# 必须在 import app 之前
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("AGENT_DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test.db")
os.environ.setdefault("LOCAL_STORAGE_DIR", "./data/storage-test")

Path("./data").mkdir(parents=True, exist_ok=True)
