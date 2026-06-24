"""
Me — 核心配置
"""
import os
from pathlib import Path

ME_HOME     = Path(os.environ.get("ME_HOME", "/app/me_data"))
DB_PATH     = ME_HOME / "me.db"
REPORTS_DIR = ME_HOME / "reports"
SKILLS_DIR  = Path(os.environ.get("SKILLS_DIR", str(ME_HOME / "skills")))
UPLOAD_DIR  = ME_HOME / "uploads"
CHROMA_PATH = ME_HOME / "chroma"
STATIC_DIR  = Path(os.environ.get("ME_STATIC_DIR", "/app/static"))

LLM_BASE    = os.environ.get("LLM_API_BASE", "http://192.168.1.100:11434/v1")
LLM_MODEL   = os.environ.get("LLM_MODEL", "")
MAX_PARSE_CHARS = 200000

for p in [DB_PATH.parent, REPORTS_DIR, CHROMA_PATH, UPLOAD_DIR]:
    p.mkdir(parents=True, exist_ok=True)
