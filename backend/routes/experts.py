"""
Experts API — 专家管理系统
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.config import SKILLS_DIR

logger = logging.getLogger("me-backend")
router = APIRouter()


class ExpertOut(BaseModel):
    id: str
    name: str
    avatar: str
    domain: str
    summon_phrase: str = ""
    response_phrase: str = ""
    system_prompt: str = ""
    is_enabled: bool = True

    class Config:
        from_attributes = True


# ─── 读 prompt 文件 ─────────────────────────────

def _read_prompt_file(expert_id: str) -> str:
    """读取 expert 的人格文件"""
    path = SKILLS_DIR / "me_experts" / f"{expert_id}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    # fallback: 旧路径
    from core.config import ME_HOME
    path2 = ME_HOME / "skills" / "me_experts" / f"{expert_id}.md"
    if path2.exists():
        return path2.read_text(encoding="utf-8")
    return ""


def _write_prompt_file(expert_id: str, content: str):
    """写入 expert 的人格文件"""
    path = SKILLS_DIR / "me_experts" / f"{expert_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ─── API ─────────────────────────────────────────

@router.get("/experts")
def list_experts():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM experts ORDER BY CASE id WHEN 'taishiling' THEN 0 ELSE 1 END, id"
    ).fetchall()
    db.close()
    return [
        ExpertOut(
            id=r["id"], name=r["name"], avatar=r["avatar"], domain=r["domain"],
            summon_phrase=r["summon_phrase"] or "",
            response_phrase=r["response_phrase"] or "",
            system_prompt="",
            is_enabled=bool(r["is_enabled"]),
        ).model_dump()
        for r in rows
    ]


@router.get("/experts/{expert_id}")
def get_expert(expert_id: str):
    db = get_db()
    r = db.execute("SELECT * FROM experts WHERE id=?", [expert_id]).fetchone()
    db.close()
    if not r:
        raise HTTPException(404, "Expert not found")
    prompt = _read_prompt_file(expert_id)
    return ExpertOut(
        id=r["id"], name=r["name"], avatar=r["avatar"], domain=r["domain"],
        summon_phrase=r["summon_phrase"] or "",
        response_phrase=r["response_phrase"] or "",
        system_prompt=prompt,
        is_enabled=bool(r["is_enabled"]),
    ).model_dump()


@router.post("/experts")
def create_expert(body: dict):
    eid = body.get("id", "").strip().lower().replace(" ", "_")
    if not eid:
        eid = f"custom_{uuid.uuid4().hex[:8]}"
    name = body.get("name", "新专家")
    avatar = body.get("avatar", "🤖")
    domain = body.get("domain", "")
    summon = body.get("summon_phrase", "")
    resp = body.get("response_phrase", "")
    system_prompt = body.get("system_prompt", "")

    _write_prompt_file(eid, system_prompt or f"# {name}\n\n待编辑人格设定...")
    file_path = SKILLS_DIR / "me_experts" / f"{eid}.md"

    db = get_db()
    db.execute(
        """INSERT INTO experts(id,name,avatar,domain,summon_phrase,response_phrase,system_prompt_file)
           VALUES(?,?,?,?,?,?,?)""",
        [eid, name, avatar, domain, summon, resp, str(file_path)]
    )
    db.commit()
    db.close()
    return {"ok": True, "id": eid, "name": name}


@router.put("/experts/{expert_id}")
def update_expert(expert_id: str, body: dict):
    db = get_db()
    existing = db.execute("SELECT id FROM experts WHERE id=?", [expert_id]).fetchone()
    if not existing:
        db.close()
        raise HTTPException(404, "Expert not found")

    fields = {k: body.get(k) for k in ["name", "avatar", "summon_phrase",
                                        "response_phrase", "domain", "is_enabled"]
              if k in body}
    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        db.execute(f"UPDATE experts SET {sets} WHERE id=?", list(fields.values()) + [expert_id])

    if "system_prompt" in body:
        _write_prompt_file(expert_id, body["system_prompt"])

    db.commit()
    db.close()
    return {"ok": True}


@router.post("/experts/{expert_id}/reset")
def reset_expert(expert_id: str):
    """重置专家到默认人格"""
    db = get_db()
    r = db.execute("SELECT * FROM experts WHERE id=?", [expert_id]).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "Expert not found")

    defaults = {
        "taishiling": ("📜", "all", "史官在侧，秉笔直书。", "太史令在此。你的言行，我将如实录于竹帛。"),
        "zhongkui": ("⚔️", "自我核心", "三尺青锋，照我肝胆。", "心中有鬼，方须照剑。你是来伏魔的，还是来求饶的？"),
        "chiyou": ("🐉", "事业", "兵主旗下，雾散云开。", "说敌情。畏刀避剑之人，不配站在我的旗下。"),
        "bigan": ("⚖️", "财富", "玲珑七窍，公断无私。", "我无心，故不偏。把你那笔糊涂账，摊开来。"),
        "tanlang": ("🐺", "人性", "贪狼吞月，欲念昭然。", "你身上每一寸欲望，都瞒不过我。说吧，这次想喂养哪一个？"),
        "zaojun": ("🔥", "亲密关系", "灶火明堂，司命在场。", "家宅之事，善恶功过，我记下了。从实道来。"),
        "qibo": ("🌿", "健康", "上古天真，问于天师。", "身乃心之宅。你哪里失了调和，从实说来。"),
        "cangjie": ("🏺", "自知", "鸟兽蹄爪，皆有其迹。", "你看到了什么？是河底的石头，还是水面上的波纹？"),
    }
    if expert_id in defaults:
        avatar, domain, summon, resp = defaults[expert_id]
        db.execute(
            "UPDATE experts SET avatar=?, domain=?, summon_phrase=?, response_phrase=?, is_enabled=1 WHERE id=?",
            [avatar, domain, summon, resp, expert_id]
        )
        # 重置 prompt 文件
        from context.assembly import EXPERT_PROMPTS
        prompt = EXPERT_PROMPTS.get(expert_id, "")
        if prompt:
            _write_prompt_file(expert_id, prompt)
    db.commit()
    db.close()
    return {"ok": True, "message": f"{expert_id} 已重置"}
