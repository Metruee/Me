"""
Me — 数据库连接与初始化
"""
import sqlite3
import threading
from typing import Optional
from .config import DB_PATH

_local = threading.local()

def close_db():
    """关闭当前线程的数据库连接"""
    if hasattr(_local, "conn") and _local.conn is not None:
        try:
            _local.conn.close()
        except:
            pass
        _local.conn = None

def get_db() -> sqlite3.Connection:
    """获取（线程级）数据库连接"""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    else:
        try:
            _local.conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            _local.conn = sqlite3.connect(str(DB_PATH))
            _local.conn.row_factory = sqlite3.Row
            _local.conn.execute("PRAGMA journal_mode=WAL")
            _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn

def init_db():
    """初始化数据库表结构（7 张核心表）"""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL DEFAULT 'default',
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            expert_id TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_conv_expert ON conversations(expert_id);

        CREATE TABLE IF NOT EXISTS sessions(
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL DEFAULT '新对话',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_entries(
            id TEXT PRIMARY KEY,
            theme_main TEXT DEFAULT '未归类',
            summary TEXT DEFAULT '',
            original_text TEXT DEFAULT '',
            expert_id TEXT DEFAULT '',
            importance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_kb_theme ON knowledge_entries(theme_main);

        CREATE TABLE IF NOT EXISTS daoben_entries(
            id TEXT PRIMARY KEY,
            event_text TEXT DEFAULT '',
            first_reaction TEXT DEFAULT '',
            greed TEXT DEFAULT '',
            fear TEXT DEFAULT '',
            excuses TEXT DEFAULT '',
            main_stone TEXT DEFAULT '',
            tomorrow_plan TEXT DEFAULT '',
            expert_id TEXT DEFAULT '',
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports(
            id TEXT PRIMARY KEY,
            filename TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS skills(
            id TEXT PRIMARY KEY,
            label TEXT DEFAULT '',
            description TEXT DEFAULT '',
            version INTEGER DEFAULT 1,
            enabled INTEGER DEFAULT 1,
            source_path TEXT DEFAULT '',
            trust_status TEXT DEFAULT 'review_required',
            tool_ids TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS impressions(
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            content TEXT DEFAULT '',
            kind TEXT DEFAULT 'impression',
            subject TEXT DEFAULT 'user',
            expert_id TEXT DEFAULT '',
            importance INTEGER DEFAULT 0,
            source TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_imp_expert ON impressions(expert_id);

        CREATE TABLE IF NOT EXISTS event_records(
            id TEXT PRIMARY KEY,
            session_id TEXT DEFAULT '',
            expert_id TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            content TEXT DEFAULT '',
            theme TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()
