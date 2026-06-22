"""
Config API — 兼容原始 /api/config 路径
"""
import logging
from fastapi import APIRouter
from core.db import get_db

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/config")
def get_config():
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    db.close()
    return {r["key"]: r["value"] for r in rows}


@router.put("/config")
def update_config(body: dict):
    db = get_db()
    for k, v in body.items():
        db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?",
            [k, str(v), str(v)]
        )
    db.commit()
    db.close()
    return {"ok": True}
