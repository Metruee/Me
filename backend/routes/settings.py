from __future__ import annotations
"""
Settings API
"""
import logging
from fastapi import APIRouter
from core.db import get_db

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/settings")
def get_settings():
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    db.close()
    return {r["key"]: r["value"] for r in rows}


@router.get("/settings/{key}")
def get_setting(key: str):
    db = get_db()
    r = db.execute("SELECT value FROM settings WHERE key=?", [key]).fetchone()
    db.close()
    return {"key": key, "value": r["value"] if r else ""}


@router.put("/settings/{key}")
def update_setting(key: str, body: dict):
    value = body.get("value", "")
    db = get_db()
    db.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?",
        [key, value, value]
    )
    db.commit()
    db.close()
    return {"ok": True}
