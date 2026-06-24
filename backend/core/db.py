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
        CREATE TABLE IF NOT EXISTS experts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            system_prompt_file TEXT DEFAULT '',
            summon_phrase TEXT DEFAULT '',
            response_phrase TEXT DEFAULT '',
            domain TEXT DEFAULT 'all',
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
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
    # -- Schema migration: skills 表旧版 (name/has_manifest) → 新版 (label/description/...) --
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(skills)").fetchall()]
        if "label" not in cols:
            db.executescript(
                "ALTER TABLE skills RENAME TO skills_old;"
                "CREATE TABLE skills("
                "  id TEXT PRIMARY KEY,"
                "  label TEXT DEFAULT '',"
                "  description TEXT DEFAULT '',"
                "  version INTEGER DEFAULT 1,"
                "  enabled INTEGER DEFAULT 1,"
                "  source_path TEXT DEFAULT '',"
                "  trust_status TEXT DEFAULT 'review_required',"
                "  tool_ids TEXT DEFAULT '',"
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ");"
                "INSERT INTO skills(id, label, enabled, created_at)"
                "  SELECT id, name, enabled, created_at FROM skills_old;"
                "DROP TABLE skills_old;"
            )
            db.commit()
    except Exception:
        pass

    # Seed default settings
    from .config import LLM_BASE, LLM_MODEL
    defaults = [
        ("llm_api_base", LLM_BASE),
        ("llm_model", LLM_MODEL),
        ("embedding_api_base", LLM_BASE),
        ("embedding_model", ""),
        ("auto_archive", "true"),
        ("similarity_threshold", "0.6"),
        ("chat_history_rounds", "10"),
    ]
    for k, v in defaults:
        db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", [k, v])

    # Seed default experts
    experts_seed = [
        ("taishiling","太史令","📜","all","史官在侧，秉笔直书。","太史令在此。你的言行，我将如实录于竹帛。"),
        ("zhongkui","钟馗","⚔️","自我核心","三尺青锋，照我肝胆。","心中有鬼，方须照剑。你是来伏魔的，还是来求饶的？"),
        ("chiyou","蚩尤","🐉","事业","兵主旗下，雾散云开。","说敌情。畏刀避剑之人，不配站在我的旗下。"),
        ("bigan","比干","⚖️","财富","玲珑七窍，公断无私。","我无心，故不偏。把你那笔糊涂账，摊开来。"),
        ("tanlang","贪狼","🐺","人性","贪狼吞月，欲念昭然。","你身上每一寸欲望，都瞒不过我。说吧，这次想喂养哪一个？"),
        ("zaojun","司命灶君","🔥","亲密关系","灶火明堂，司命在场。","家宅之事，善恶功过，我记下了。从实道来。"),
        ("qibo","岐伯","🌿","健康","上古天真，问于天师。","身乃心之宅。你哪里失了调和，从实说来。"),
        ("cangjie","仓颉","🏺","自知","鸟兽蹄爪，皆有其迹。","你看到了什么？是河底的石头，还是水面上的波纹？"),
    ]
    from core.config import SKILLS_DIR
    for eid, name, avatar, domain, summon, resp in experts_seed:
        skill_file = f"{SKILLS_DIR}/me_experts/{eid}.md"
        db.execute(
            "INSERT OR IGNORE INTO experts(id,name,avatar,domain,summon_phrase,response_phrase,system_prompt_file) VALUES(?,?,?,?,?,?,?)",
            [eid, name, avatar, domain, summon, resp, skill_file]
        )
    db.commit()
