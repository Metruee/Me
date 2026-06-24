from __future__ import annotations
"""
三区记忆系统（参考 Zleap-Agent 设计）

A 线 — notes（印象/经验）: 主动写入，最近 N 条，无模型
B 线 — records（事件记录）: 对话抽取 + 召回
C 线 — 经验沉淀: 从报告和模式中提取

Context 组装原则：prefetch 只做快速读取（A 最近 N + B 最近 record），不走 LLM；
主动 recall 才用 precise（LLM 精排）。
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from core.db import get_db, close_db as _close_db
from providers.registry import llm, embedding

logger = logging.getLogger("me-backend")

NOTE_LIMIT = 20  # 每条线最大保留条数


# ═══════════════════════════════════════════════════════════
#  A 线 — 印象/经验 notes
# ═══════════════════════════════════════════════════════════

def write_note(kind: str, title: str, content: str,
               subject: str = "user", expert_id: str = "",
               importance: int = 0,
               source: str = "chat") -> dict:
    """写入一条印象/经验（A 线）。超出 NOTE_LIMIT 时淘汰最旧的。"""
    import uuid
    note_id = f"note_{uuid.uuid4().hex[:12]}"
    db = get_db()
    db.execute(
        """INSERT INTO impressions(id, title, content, kind, subject, expert_id, importance, source, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [note_id, title, content, kind, subject, expert_id, importance, source,
         datetime.now(timezone.utc).isoformat()]
    )
    # 淘汰超出限制的旧记录
    db.execute(
        f"DELETE FROM impressions WHERE kind=? AND id NOT IN "
        f"(SELECT id FROM impressions WHERE kind=? ORDER BY created_at DESC LIMIT {NOTE_LIMIT})",
        [kind, kind]
    )
    db.commit()
    _close_db()
    return {"id": note_id, "kind": kind, "title": title, "content": content}

def list_notes(kind: str = "", expert_id: str = "", limit: int = NOTE_LIMIT) -> list:
    """列出笔记。kind/expert_id 为空则列出全部。"""
    import sqlite3
    from core.config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        conditions = []
        params = []
        if kind:
            conditions.append("kind=?")
            params.append(kind)
        if expert_id:
            conditions.append("expert_id=?")
            params.append(expert_id)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM impressions{where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_note_by_id(note_id: str) -> Optional[dict]:
    import sqlite3
    from core.config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        r = conn.execute("SELECT * FROM impressions WHERE id=?", [note_id]).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def delete_note(note_id: str):
    import sqlite3
    from core.config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("DELETE FROM impressions WHERE id=?", [note_id])
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  B 线 — 事件记录（对话记录持久化）
# ═══════════════════════════════════════════════════════════

def write_event_record(session_id: str, expert_id: str,
                       summary: str, content: str, theme: str = "") -> dict:
    """从对话中提取并保存一条事件记录（B 线）。"""
    import uuid
    rid = f"evt_{uuid.uuid4().hex[:12]}"
    db = get_db()
    db.execute(
        """INSERT INTO event_records(id, session_id, expert_id, summary, content, theme, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [rid, session_id, expert_id, summary, content, theme,
         datetime.now(timezone.utc).isoformat()]
    )
    db.commit()
    _close_db()
    return {"id": rid, "summary": summary}

def list_event_records(limit: int = 20, expert_id: str = "") -> list:
    import sqlite3
    from core.config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        if expert_id:
            rows = conn.execute(
                "SELECT * FROM event_records WHERE expert_id=? ORDER BY created_at DESC LIMIT ?",
                [expert_id, limit]
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM event_records ORDER BY created_at DESC LIMIT ?",
                [limit]
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  Context Prefetch（快速预取，不走 LLM）
# ═══════════════════════════════════════════════════════════

def prefetch_context(expert_id: str = "") -> dict:
    """快速预取记忆上下文区块（无 LLM 调用），按 expert_id 隔离"""
    impressions = list_notes(kind="impression", expert_id=expert_id, limit=NOTE_LIMIT)
    experiences = list_notes(kind="experience", expert_id=expert_id, limit=NOTE_LIMIT)
    recent_records = list_event_records(expert_id=expert_id, limit=5)
    return {
        "impressions": impressions,
        "experiences": experiences,
        "recent_records": recent_records,
    }

def format_context_blocks(expert_id: str = "") -> str:
    """将记忆拼装为 system prompt 插入到对话中（stable 区块），按 expert_id 隔离"""
    ctx = prefetch_context(expert_id=expert_id)
    blocks = []
    if ctx["impressions"]:
        lines = [f"- [{n['created_at'][:10]}] {n['title']}: {n['content'][:200]}"
                 for n in ctx["impressions"]]
        blocks.append("## 我对这个人的印象\n" + "\n".join(lines))
    if ctx["experiences"]:
        lines = [f"- [{n['created_at'][:10]}] {n['title']}: {n['content'][:200]}"
                 for n in ctx["experiences"]]
        blocks.append("## 已沉淀的经验\n" + "\n".join(lines))
    if ctx["recent_records"]:
        lines = [f"- [{r['created_at'][:10]}] {r['summary'][:150]}"
                 for r in ctx["recent_records"]]
        blocks.append("## 最近事件\n" + "\n".join(lines))
    return "\n\n".join(blocks)


# ═══════════════════════════════════════════════════════════
#  从对话中自动抽取印象 / 事件
# ═══════════════════════════════════════════════════════════

def extract_impression_from_chat(session_id: str, expert_id: str,
                                 user_message: str, reply: str):
    """用 LLM 从对话中提取印象，异步调用"""
    import threading
    def _do():
        try:
            if not llm.is_configured():
                return
            prompt = (
                "从以下对话中提取一条关于用户的关键印象（性格特质、偏好、行为模式）。\n"
                "如果无明显信息，返回空。\n"
                "JSON格式: {\"title\": \"简短标题\", \"content\": \"印象描述（<100字）\", \"importance\": 0-5}\n\n"
                f"用户: {user_message[:500]}\n专家: {reply[:500]}"
            )
            result = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=200
            )
            text = result.get("content", "").strip()
            if text:
                # 尝试解析 JSON
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                data = json.loads(text)
                if data.get("title") and data.get("content"):
                    write_note(
                        kind="impression",
                        title=data["title"],
                        content=data["content"][:500],
                        expert_id=expert_id,
                        importance=data.get("importance", 1),
                        source="chat",
                    )
        except Exception as e:
            logger.debug(f"Impression extraction skipped: {e}")
    threading.Thread(target=_do, daemon=True).start()


def extract_event_from_chat(session_id: str, expert_id: str,
                            user_message: str, reply: str):
    """用 LLM 提取关键事件记录"""
    import threading
    def _do():
        try:
            if not llm.is_configured():
                return
            prompt = (
                "以下对话是否提到了某个具体事件、事实、决定或进展？"
                "如果有，用JSON提取。如果没有，返回空JSON {}。\n"
                "JSON: {\"summary\": \"一句话摘要\", \"theme\": \"事件主题\"}\n\n"
                f"用户: {user_message[:500]}\n专家: {reply[:500]}"
            )
            result = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=200
            )
            text = result.get("content", "").strip()
            if text and "summary" in text:
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                data = json.loads(text)
                if data.get("summary"):
                    write_event_record(
                        session_id=session_id,
                        expert_id=expert_id,
                        summary=data["summary"],
                        content=f"用户: {user_message[:300]}\n专家: {reply[:300]}",
                        theme=data.get("theme", ""),
                    )
        except Exception as e:
            logger.debug(f"Event extraction skipped: {e}")
    threading.Thread(target=_do, daemon=True).start()
