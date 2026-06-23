from __future__ import annotations
"""
Settings API
"""
import logging
import os
import yaml
from pathlib import Path
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
    _sync_to_config(key, value)
    db = get_db()
    db.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?",
        [key, value, value]
    )
    db.commit()
    db.close()
    return {"ok": True}

def _sync_to_config(key: str, value: str):
    """将 Settings UI 的配置同步到 config.yaml"""
    try:
        me_home = os.environ.get("ME_HOME", "/app/me_data")
        cfg_path = Path(me_home) / "config.yaml"
        if not cfg_path.exists():
            return
        raw = cfg_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
        mapping = {
            "llm_api_base": ("provider", "base_url"),
            "llm_model": ("provider", "model"),
            "llm_api_key": ("provider", "api_key"),
            "embedding_api_base": ("memory", "embedding_base_url"),
            "embedding_model": ("memory", "embedding_model"),
        }
        if key not in mapping:
            return
        section, field = mapping[key]
        if section not in data:
            data[section] = {}
        if not isinstance(data[section], dict):
            data[section] = {}
        data[section][field] = value
        with open(str(cfg_path), "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        logger.info(f"Config synced: config.yaml {section}.{field} = {value}")
    except Exception as e:
        logger.warning(f"Config sync failed: {e}")


