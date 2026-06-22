from __future__ import annotations
"""
档案馆（知识库）API
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from core.db import get_db
from core.models import KnowledgeEntryOut, KnowledgeUpdate

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/knowledge")
def list_knowledge(
    theme: str = "",
    search: str = "",
    limit: int = 100,
    offset: int = 0,
):
    db = get_db()
    sql = "SELECT * FROM knowledge_entries WHERE 1=1"
    params = []
    if theme:
        sql += " AND theme_main=?"
        params.append(theme)
    if search:
        sql += " AND (summary LIKE ? OR original_text LIKE ?)"
        q = f"%{search}%"
        params.extend([q, q])
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return {"entries": [dict(r) for r in rows], "total": len(rows)}


@router.get("/knowledge/themes")
def list_themes():
    db = get_db()
    rows = db.execute(
        "SELECT theme_main, COUNT(*) as count FROM knowledge_entries GROUP BY theme_main ORDER BY count DESC"
    ).fetchall()
    db.close()
    return [{"theme": r["theme_main"], "count": r["count"]} for r in rows]


@router.get("/knowledge/{entry_id}")
def get_knowledge_entry(entry_id: str):
    db = get_db()
    r = db.execute("SELECT * FROM knowledge_entries WHERE id=?", [entry_id]).fetchone()
    db.close()
    if not r:
        raise HTTPException(404)
    return dict(r)


@router.put("/knowledge/{entry_id}")
def update_knowledge_entry(entry_id: str, body: KnowledgeUpdate):
    db = get_db()
    if body.theme_main is not None:
        db.execute("UPDATE knowledge_entries SET theme_main=? WHERE id=?", [body.theme_main, entry_id])
    if body.summary is not None:
        db.execute("UPDATE knowledge_entries SET summary=? WHERE id=?", [body.summary, entry_id])
    db.commit()
    db.close()
    return {"ok": True}


@router.delete("/knowledge/{entry_id}")
def delete_knowledge_entry(entry_id: str):
    db = get_db()
    db.execute("DELETE FROM knowledge_entries WHERE id=?", [entry_id])
    db.commit()
    db.close()
    try:
        import chromadb
        from core.config import CHROMA_PATH
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        coll = client.get_collection("me_knowledge")
        coll.delete(ids=[entry_id])
    except:
        pass
    return {"ok": True}


@router.delete("/knowledge/clear")
def clear_knowledge():
    db = get_db()
    db.execute("DELETE FROM knowledge_entries")
    db.commit()
    db.close()
    return {"ok": True}
