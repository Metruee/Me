"""
Me — Pydantic 数据模型
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

# ─── Expert ─────────────────────────────────────────
EXPERT_DOMAINS = {
    "taishiling": "all",
    "zhongkui": "自我核心",
    "chiyou": "事业",
    "bigan": "财富",
    "tanlang": "人性",
    "zaojun": "亲密关系",
    "qibo": "健康",
    "cangjie": "自知",
}

EXPERT_SUMMON = {
    "taishiling": "太史令",
    "zhongkui": "钟馗",
    "chiyou": "蚩尤",
    "bigan": "比干",
    "tanlang": "贪狼",
    "zaojun": "司命灶君",
    "qibo": "七魄",
    "cangjie": "仓颉",
}

# ─── Chat ───────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    expert_id: str = "taishiling"
    session_id: str = "default"
    is_file_upload: bool = False

class ChatResponse(BaseModel):
    reply: str = ""
    expert_id: str = ""
    switch_type: str = "none"
    system_message: str = ""
    archived: bool = False
    llm_error: str = ""

# ─── Sessions ───────────────────────────────────────
class SessionCreate(BaseModel):
    id: Optional[str] = None

class SessionRename(BaseModel):
    label: str = Field(..., min_length=1)

# ─── Knowledge ──────────────────────────────────────
class KnowledgeEntryOut(BaseModel):
    id: str
    theme_main: str = "未归类"
    summary: str = ""
    original_text: str = ""
    expert_id: str = ""
    created_at: str = ""

class KnowledgeUpdate(BaseModel):
    theme_main: Optional[str] = None
    summary: Optional[str] = None

# ─── Daoben ─────────────────────────────────────────
class DaobenEntryIn(BaseModel):
    event_text: str = ""
    first_reaction: str = ""
    greed: str = ""
    fear: str = ""
    excuses: str = ""
    main_stone: str = ""
    tomorrow_plan: str = ""
    expert_id: str = ""
    source: str = "manual"

class DaobenEntryOut(BaseModel):
    id: str
    event_text: str = ""
    first_reaction: str = ""
    greed: str = ""
    fear: str = ""
    excuses: str = ""
    main_stone: str = ""
    tomorrow_plan: str = ""
    expert_id: str = ""
    source: str = "manual"
    created_at: str = ""

# ─── Impressions (记忆-印象区) ──────────────────────
class ImpressionCreate(BaseModel):
    title: str
    content: str
    kind: str = "impression"  # impression | experience
    subject: str = "user"
    expert_id: str = ""
    importance: int = 0
    source: str = "chat"

# ─── Report ─────────────────────────────────────────
class ReportRequest(BaseModel):
    kind: str = "manual"  # manual | weekly | monthly
