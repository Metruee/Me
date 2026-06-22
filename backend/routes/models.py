"""
Models API — 拉取可用模型列表
"""
import json
import logging
import urllib.request
from fastapi import APIRouter
from core.db import get_db
from core.config import LLM_BASE, LLM_MODEL

logger = logging.getLogger("me-backend")
router = APIRouter()


def _resolve_llm_config() -> tuple:
    db = get_db()
    api, model = LLM_BASE, LLM_MODEL
    try:
        r1 = db.execute("SELECT value FROM settings WHERE key='llm_api_base'").fetchone()
        r2 = db.execute("SELECT value FROM settings WHERE key='llm_model'").fetchone()
        if r1 and r1["value"]:
            api = r1["value"]
        if r2 and r2["value"]:
            model = r2["value"]
    except:
        pass
    db.close()
    return api, model


@router.get("/models")
def list_models(include_embedding: bool = False):
    api_base, model = _resolve_llm_config()
    if not api_base:
        return {"ok": True, "models": [], "embedding_models": [], "error": "LLM API 地址未配置"}
    base = api_base.rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            models = [m["id"] for m in data.get("data", []) if "id" in m]
    except Exception as e:
        logger.warning(f"Failed to fetch models: {e}")
        return {"ok": True, "models": [], "embedding_models": [], "error": f"无法拉取模型列表: {e}"}

    embedding_models = []
    if include_embedding:
        # 尝试拉取 embedding 模型
        db = get_db()
        try:
            r = db.execute("SELECT value FROM settings WHERE key='embedding_api_base'").fetchone()
            emb_base = (r["value"] if r else "") or api_base
            db.close()
            if emb_base:
                req2 = urllib.request.Request(f"{emb_base.rstrip('/')}/models")
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    data2 = json.loads(resp2.read())
                    embedding_models = [m["id"] for m in data2.get("data", []) if "id" in m]
        except:
            db.close()
            embedding_models = [m for m in models if "embed" in m.lower()]

    current_model = model or (models[0] if models else "")
    return {
        "ok": True,
        "models": models,
        "embedding_models": embedding_models,
        "current_model": current_model,
    }
