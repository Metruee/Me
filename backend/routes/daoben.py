from __future__ import annotations
"""
道痕日记 API
"""
import logging
import uuid as _uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from core.db import get_db
from core.models import DaobenEntryOut, DaobenEntryIn

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/daoben/entries")
def list_daoben(search: str = "", limit: int = 50, offset: int = 0):
    db = get_db()
    sql = "SELECT * FROM daoben_entries WHERE 1=1"
    params = []
    if search:
        sql += " AND (event_text LIKE ? OR main_stone LIKE ? OR greed LIKE ? OR fear LIKE ?)"
        q = f"%{search}%"
        params.extend([q, q, q, q])
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/daoben/entries/{entry_id}")
def get_daoben_entry(entry_id: str):
    db = get_db()
    r = db.execute("SELECT * FROM daoben_entries WHERE id=?", [entry_id]).fetchone()
    db.close()
    if not r:
        raise HTTPException(404, "道痕条目不存在")
    return dict(r)


@router.post("/daoben/entries")
def create_daoben_entry(body: dict):
    entry_id = body.get("id") or f"daoben_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    db = get_db()
    db.execute(
        """INSERT INTO daoben_entries(id,event_text,first_reaction,greed,fear,excuses,main_stone,tomorrow_plan,expert_id,source)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        [
            entry_id, body.get("event_text", ""), body.get("first_reaction", ""),
            body.get("greed", ""), body.get("fear", ""), body.get("excuses", ""),
            body.get("main_stone", ""), body.get("tomorrow_plan", ""),
            body.get("expert_id", ""), body.get("source", "manual"),
        ]
    )
    db.commit()
    db.close()
    return {"ok": True, "id": entry_id}


@router.delete("/daoben/entries/{entry_id}")
def delete_daoben_entry(entry_id: str):
    db = get_db()
    db.execute("DELETE FROM daoben_entries WHERE id=?", [entry_id])
    db.commit()
    db.close()
    return {"ok": True}


@router.get("/daoben/dashboard")
def daoben_dashboard(period: str = "week"):
    db = get_db()
    now = datetime.now(timezone.utc)
    since = None
    if period == "week":
        since = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    elif period == "month":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

    base_sql = "SELECT * FROM daoben_entries"
    params = []
    if since:
        base_sql += " WHERE created_at >= ?"
        params.append(since)
    base_sql += " ORDER BY created_at DESC"
    rows = db.execute(base_sql, params).fetchall()
    db.close()

    total = len(rows)
    if total == 0:
        return {"total": 0, "stones": [], "greed_fear_ratio": None,
                "excuses": [], "timeline": [], "trend": "stable",
                "trend_label": "暂无道痕记录"}

    stone_count = {}
    for r in rows:
        s = (r["main_stone"] or "").strip()
        if s:
            stone_count[s] = stone_count.get(s, 0) + 1
    stones = sorted(
        [{"stone": k, "count": v} for k, v in stone_count.items()],
        key=lambda x: x["count"], reverse=True
    )[:10]
    has_greed = sum(1 for r in rows if (r["greed"] or "").strip())
    has_fear = sum(1 for r in rows if (r["fear"] or "").strip())
    greed_fear_ratio = round(has_greed / max(has_fear, 1), 2)
    excuse_count = {}
    for r in rows:
        e = (r["excuses"] or "").strip()
        if e:
            excuse_count[e] = excuse_count.get(e, 0) + 1
    excuses = sorted(
        [{"excuse": k, "count": v} for k, v in excuse_count.items()],
        key=lambda x: x["count"], reverse=True
    )[:5]
    daily = {}
    for r in rows:
        day = (r["created_at"] or "")[:10]
        if day:
            daily[day] = daily.get(day, 0) + 1
    timeline = [{"date": k, "count": v} for k, v in sorted(daily.items())]
    trend = "stable"
    if len(stones) >= 2:
        top_pct = stones[0]["count"] / total
        if top_pct > 0.5:
            trend = "dominated"
        elif top_pct > 0.3:
            trend = "skewed"
    return {
        "total": total, "period": period, "stones": stones,
        "greed_fear_ratio": greed_fear_ratio,
        "greed_fear_label": "贪多惧少" if greed_fear_ratio > 1.5
        else ("惧多贪少" if greed_fear_ratio < 0.67 else "贪惧均衡"),
        "excuses": excuses, "timeline": timeline, "trend": trend,
        "trend_label": {"stable": "心石分布均匀", "skewed": "某类心石偏高",
                       "dominated": "单一心石主导"}.get(trend, ""),
    }


@router.get("/daoben/stats")
def daoben_stats():
    db = get_db()
    rows = db.execute(
        "SELECT main_stone, COUNT(*) as cnt FROM daoben_entries WHERE main_stone != '' GROUP BY main_stone ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    db.close()
    return [{"stone": r["main_stone"], "count": r["cnt"]} for r in rows]
