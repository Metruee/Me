from __future__ import annotations
"""
三区记忆 API — 印象/事件/经验的 CRUD 接口
"""
import logging
from fastapi import APIRouter, HTTPException
from core.models import ImpressionCreate
from memory.orchestrator import (
    write_note, list_notes, get_note_by_id, delete_note,
    list_event_records,
)

logger = logging.getLogger("me-backend")
router = APIRouter()


# ─── 印象/经验区（A 线） ────────────────────────

@router.get("/memory/notes")
def get_notes(kind: str = "", expert_id: str = "", limit: int = 20):
    return {"notes": list_notes(kind=kind, expert_id=expert_id, limit=limit)}


@router.post("/memory/notes")
def create_note(body: ImpressionCreate):
    result = write_note(
        kind=body.kind,
        title=body.title,
        content=body.content,
        subject=body.subject,
        expert_id=body.expert_id,
        importance=body.importance,
        source=body.source,
    )
    return {"ok": True, "note": result}


@router.get("/memory/notes/{note_id}")
def get_note(note_id: str):
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(404)
    return note


@router.delete("/memory/notes/{note_id}")
def remove_note(note_id: str):
    delete_note(note_id)
    return {"ok": True}


# ─── 事件记录区（B 线） ────────────────────────

@router.get("/memory/events")
def get_events(limit: int = 20, expert_id: str = ""):
    return {"events": list_event_records(limit=limit, expert_id=expert_id)}


# ─── 记忆上下文预取 ─────────────────────────────

@router.get("/memory/context")
def get_memory_context(expert_id: str = ""):
    """快速预取所有记忆区块（无 LLM），按 expert_id 隔离"""
    from memory.orchestrator import prefetch_context
    return prefetch_context(expert_id=expert_id)
