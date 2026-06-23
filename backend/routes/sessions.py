"""
Sessions API
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from core.db import get_db
from core.models import SessionCreate, SessionRename

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.post("/sessions")
def create_session(body: SessionCreate):
    db = get_db()
    d = datetime.now()
    label = f"对话 {d.month}/{d.day} {d.hour}:{str(d.minute).zfill(2)}"
    import uuid
    sid = body.id or uuid.uuid4().hex[:12]
    # 使用 INSERT OR IGNORE 处理 ID 冲突
    db.execute(
        "INSERT OR IGNORE INTO sessions(id, label, created_at) VALUES (?, ?, ?)",
        [sid, label, datetime.now(timezone.utc).isoformat()]
    )
    db.commit()
    db.close()
    return {"ok": True, "id": sid}


@router.get("/sessions")
def list_sessions():
    db = get_db()
    rows = db.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 50").fetchall()
    db.close()
    return [{"id": r["id"], "label": r["label"], "date": r["created_at"][:10] if r["created_at"] else ""}
            for r in rows]


@router.put("/sessions/{session_id}")
def rename_session(session_id: str, body: SessionRename):
    db = get_db()
    db.execute("UPDATE sessions SET label=? WHERE id=?", [body.label, session_id])
    db.commit()
    db.close()
    return {"ok": True}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    db = get_db()
    db.execute("DELETE FROM conversations WHERE session_id=?", [session_id])
    db.execute("DELETE FROM sessions WHERE id=?", [session_id])
    db.commit()
    db.close()
    return {"ok": True}


@router.get("/sessions/{session_id}/history")
def get_session_history(session_id: str, limit: int = 200):
    db = get_db()
    rows = db.execute(
        "SELECT role, content, expert_id, created_at FROM conversations WHERE session_id=? ORDER BY id ASC",
        [session_id]
    ).fetchall()[:limit]
    db.close()
    return [dict(r) for r in rows]


@router.delete("/sessions/{session_id}/history")
def clear_session_history(session_id: str):
    db = get_db()
    db.execute("DELETE FROM conversations WHERE session_id=?", [session_id])
    db.commit()
    db.close()
    return {"ok": True}
