from __future__ import annotations
"""
技能系统 API（升级版：支持 SKILL.md 格式 + 信任审查 + 模板生成）
"""
import json
import logging
import shutil
import zipfile
import io
import yaml
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from core.db import get_db
from core.config import SKILLS_DIR

logger = logging.getLogger("me-backend")
router = APIRouter()


def _read_skill_frontmatter(skill_path: Path) -> dict:
    """读取 SKILL.md 的 YAML frontmatter"""
    try:
        text = skill_path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1]) or {}
    except:
        pass
    return {}


def _generate_skill_template(name: str, description: str) -> str:
    """生成 SKILL.md 模板"""
    return f"""---
name: {name}
description: {description}
version: 1
tools: []
trust_status: review_required
invocation_policy: implicit
---

# {name}

## 使用场景
<!-- 描述这个技能在什么场景下被触发 -->

## 工作方式
<!-- 描述技能的执行步骤 -->

## 注意事项
<!-- 安全边界和注意事项 -->
"""


@router.get("/skills")
def list_skills():
    db = get_db()
    rows = db.execute("SELECT * FROM skills ORDER BY created_at DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/skills/scan")
def scan_skills():
    """扫描 skills 目录，注册新发现的 SKILL.md"""
    if not SKILLS_DIR.exists():
        return {"skills": [], "new": 0}
    db = get_db()
    existing = {r["id"] for r in db.execute("SELECT id FROM skills").fetchall()}
    new_count = 0
    skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        skill_file = d / "SKILL.md"
        if not skill_file.exists():
            continue
        sid = d.name
        fm = _read_skill_frontmatter(skill_file)
        label = fm.get("name", sid)
        description = fm.get("description", "")
        version = fm.get("version", 1)
        trust_status = fm.get("trust_status", "review_required")
        tool_ids = json.dumps(fm.get("tools", []), ensure_ascii=False)
        if sid not in existing:
            db.execute(
                "INSERT INTO skills(id,label,description,version,enabled,source_path,trust_status,tool_ids) VALUES(?,?,?,?,1,?,?,?)",
                [sid, label, description, version, str(skill_file), trust_status, tool_ids]
            )
            new_count += 1
        else:
            db.execute(
                "UPDATE skills SET label=?,description=?,version=?,tool_ids=?,source_path=? WHERE id=?",
                [label, description, version, tool_ids, str(skill_file), sid]
            )
        skills.append({"id": sid, "label": label, "enabled": True})
    db.commit()
    db.close()
    return {"skills": skills, "new": new_count}


@router.post("/skills/install")
async def install_skill(file: UploadFile = File(...)):
    """安装技能（.zip 上传）"""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "仅支持 .zip 格式")
    zip_data = await file.read()
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    new_skills = []
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for name in zf.namelist():
            if name.endswith("SKILL.md"):
                skill_dir_name = Path(name).parent.name or Path(name).stem
                target_dir = SKILLS_DIR / skill_dir_name
                target_dir.mkdir(parents=True, exist_ok=True)
                zf.extractall(target_dir)
                new_skills.append(skill_dir_name)
    # 扫描注册
    scan_skills()
    return {"ok": True, "skills": new_skills}


@router.post("/skills/create")
def create_skill(name: str = Form(...), description: str = Form(...)):
    """创建新技能（生成 SKILL.md 模板）"""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skill_dir = SKILLS_DIR / name
    if skill_dir.exists():
        raise HTTPException(400, f"技能 {name} 已存在")
    skill_dir.mkdir(parents=True)
    template = _generate_skill_template(name, description)
    (skill_dir / "SKILL.md").write_text(template, encoding="utf-8")
    # 注册到数据库
    db = get_db()
    db.execute(
        "INSERT INTO skills(id,label,description,version,enabled,source_path,trust_status) VALUES(?,?,?,1,1,?,'review_required')",
        [name, name, description, str(skill_dir / "SKILL.md")]
    )
    db.commit()
    db.close()
    return {"ok": True, "id": name}


@router.get("/skills/{skill_id}")
def get_skill(skill_id: str):
    db = get_db()
    r = db.execute("SELECT * FROM skills WHERE id=?", [skill_id]).fetchone()
    db.close()
    if not r:
        raise HTTPException(404)
    skill_data = dict(r)
    # 读取 SKILL.md 内容
    skill_path = SKILLS_DIR / skill_id / "SKILL.md"
    if skill_path.exists():
        skill_data["content"] = skill_path.read_text(encoding="utf-8")
        fm = _read_skill_frontmatter(skill_path)
        skill_data["frontmatter"] = fm
    else:
        skill_data["content"] = ""
        skill_data["frontmatter"] = {}
    return skill_data


@router.put("/skills/{skill_id}")
def update_skill(skill_id: str, body: dict):
    db = get_db()
    if "enabled" in body:
        db.execute("UPDATE skills SET enabled=? WHERE id=?", [1 if body["enabled"] else 0, skill_id])
    if "label" in body:
        db.execute("UPDATE skills SET label=? WHERE id=?", [body["label"], skill_id])
    if "trust_status" in body:
        valid = ("trusted", "review_required", "blocked")
        if body["trust_status"] in valid:
            db.execute("UPDATE skills SET trust_status=? WHERE id=?", [body["trust_status"], skill_id])
    db.commit()
    db.close()
    return {"ok": True}


@router.put("/skills/{skill_id}/content")
def update_skill_content(skill_id: str, body: dict):
    """更新 SKILL.md 文件内容"""
    skill_path = SKILLS_DIR / skill_id / "SKILL.md"
    if not skill_path.exists():
        raise HTTPException(404)
    content = body.get("content", "")
    skill_path.write_text(content, encoding="utf-8")
    return {"ok": True}


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: str):
    db = get_db()
    r = db.execute("SELECT source_path FROM skills WHERE id=?", [skill_id]).fetchone()
    if r and r["source_path"]:
        path = Path(r["source_path"]).parent
        if path.exists():
            shutil.rmtree(path)
    db.execute("DELETE FROM skills WHERE id=?", [skill_id])
    db.commit()
    db.close()
    return {"ok": True}
