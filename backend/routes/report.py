from __future__ import annotations
"""
复盘报告 API
"""
import json
import logging
import re
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter
from core.db import get_db
from core.config import REPORTS_DIR
from providers.registry import llm

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/reports")
def list_reports():
    db = get_db()
    rows = db.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT 50").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/reports/{report_id}")
def get_report(report_id: str):
    db = get_db()
    r = db.execute("SELECT * FROM reports WHERE id=?", [report_id]).fetchone()
    db.close()
    if not r:
        return {"ok": False, "error": "报告不存在"}
    path = REPORTS_DIR / r["filename"]
    if path.exists():
        return {"ok": True, "html": path.read_text(encoding="utf-8"), "meta": dict(r)}
    return {"ok": False, "error": "文件已被删除"}


@router.delete("/reports/{report_id}")
def delete_report(report_id: str):
    db = get_db()
    r = db.execute("SELECT filename FROM reports WHERE id=?", [report_id]).fetchone()
    if r:
        path = REPORTS_DIR / r["filename"]
        if path.exists():
            path.unlink()
        db.execute("DELETE FROM reports WHERE id=?", [report_id])
        db.commit()
    db.close()
    return {"ok": True}


def _get_llm_config():
    from core.config import LLM_BASE, LLM_MODEL
    return LLM_BASE, LLM_MODEL


def _markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    html_parts = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<p><br></p>")
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            html_parts.append(f"<h{level}>{heading.group(2)}</h{level}>")
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{stripped[2:]}</li>")
            continue
        bold = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{bold}</p>")
    if in_list:
        html_parts.append("</ul>")
    return "\n".join(html_parts)


def _build_report_data(db) -> dict:
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    kb_rows = db.execute(
        "SELECT theme_main, summary, original_text, created_at FROM knowledge_entries ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    kb_total = len(kb_rows)
    by_theme = {}
    for r in kb_rows:
        theme = r["theme_main"] or "未归类"
        if theme not in by_theme:
            by_theme[theme] = []
        by_theme[theme].append({"summary": r["summary"] or "", "text": (r["original_text"] or "")[:300]})

    daoben_rows = db.execute(
        "SELECT main_stone, event_text, greed, fear, excuses, tomorrow_plan, created_at FROM daoben_entries ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    stone_freq, excuses_freq = {}, {}
    greed_count = fear_count = 0
    for r in daoben_rows:
        s = (r["main_stone"] or "").strip()
        if s:
            stone_freq[s] = stone_freq.get(s, 0) + 1
        e = (r["excuses"] or "").strip()
        if e:
            excuses_freq[e] = excuses_freq.get(e, 0) + 1
        if (r["greed"] or "").strip():
            greed_count += 1
        if (r["fear"] or "").strip():
            fear_count += 1
    top_stones = sorted(stone_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    top_excuses = sorted(excuses_freq.items(), key=lambda x: x[1], reverse=True)[:3]

    prev = db.execute(
        "SELECT id, filename, created_at FROM reports ORDER BY created_at DESC LIMIT 2"
    ).fetchall()
    prev_summary = ""
    if len(prev) >= 2:
        prev_path = REPORTS_DIR / prev[1]["filename"]
        if prev_path.exists():
            raw = prev_path.read_text(encoding="utf-8")
            text = re.sub(r'<[^>]+>', ' ', raw)
            text = re.sub(r'\s+', ' ', text).strip()
            prev_summary = text[:2000]

    return {
        "period_start": week_ago,
        "period_end": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "knowledge_total": kb_total,
        "knowledge_by_theme": {
            k: {"count": len(v), "samples": [x["summary"] for x in v[:5]]}
            for k, v in by_theme.items()
        },
        "daoben_total": len(daoben_rows),
        "top_stones": [{"stone": k, "count": v} for k, v in top_stones],
        "greed_count": greed_count,
        "fear_count": fear_count,
        "top_excuses": [{"excuse": k, "count": v} for k, v in top_excuses],
        "prev_report_summary": prev_summary,
    }


def _generate_report_analysis(report_data: dict) -> str:
    api_base, model = _get_llm_config()
    if not model:
        return "（LLM 未配置，无法生成报告）"
    data_json = json.dumps(report_data, ensure_ascii=False, indent=2)
    system_prompt = """你是「自知」平台的深度分析引擎。
自知是一个帮助人观察自己思想河流的系统。用户通过对话、记录道痕、生成知识来留下痕迹，你的任务是把这些痕迹连成镜子——让他看到自己没看到的东西。

## 分析原则
1. 基于证据：每条判断背后要有数据，可以用具体引用
2. 客观评价：不讨好、不安慰、不给鸡汤。直接说观察到的模式
3. 关注模式而非罗列：不要说"讨论了事业3次"，要说"事业讨论里反复出现同一个模式"
4. 有变化才说变化，没变化就说没变化——没有变化本身也是信息
5. 道痕和知识库要交叉验证：如果道痕里的心石和知识库里写的内容有差距，指出来
6. 温度冷静：不煽情、不制造焦虑、也不刻意淡化

## 输出格式
## 画像
一段话，≤200字。

## {领域1}
趋势：...
总结：...

## {领域2}
...

注意：领域是指 knowledge_by_theme 里的主题。道痕数据融合进画像和跨域洞察。"""

    themes = list(report_data.get("knowledge_by_theme", {}).keys())
    theme_list = "\n".join(f"- {t}" for t in themes) if themes else "（无领域数据）"
    user_prompt = f"以下是本期数据，请按格式生成报告。\n\n{data_json}"
    try:
        result = llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7, max_tokens=4096, timeout=300
        )
        return result.get("content", "") or "（LLM 返回为空）"
    except Exception as e:
        logger.warning(f"Report generation failed: {e}")
        return "（报告生成失败）"


@router.post("/reports/generate")
def generate_report():
    db = get_db()
    report_data = _build_report_data(db)
    if report_data["knowledge_total"] == 0 and report_data["daoben_total"] == 0:
        db.close()
        return {"ok": True, "message": "知识库和道痕均为空，无法生成报告"}

    report_md = _generate_report_analysis(report_data)
    report_html = _markdown_to_html(report_md)
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    period_label = f"{report_data['period_start'][:10]} ~ {report_data['period_end'][:10]}"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>Me · 复盘报告 {report_id}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin:0 auto; padding:40px 20px; color:#1c2e1c; background:#fafcfa; }}
  h1 {{ font-size:28px; border-bottom:2px solid #388e3c; padding-bottom:12px; }}
  h2 {{ font-size:20px; margin-top:32px; color:#388e3c; border-left:4px solid #388e3c; padding-left:12px; }}
  h3 {{ font-size:16px; margin-top:24px; color:#2e7d32; }}
  .report-body {{ line-height:1.9; }}
  .report-body p {{ margin:10px 0; }}
  .report-body ul {{ margin:8px 0; padding-left:20px; }}
  .meta {{ font-size:13px; color:#8a9a8a; margin-bottom:24px; }}
  .footer {{ margin-top:40px; font-size:12px; color:#8a9a8a; border-top:1px solid #d8e4d8; padding-top:12px; }}
</style></head>
<body>
  <h1>🧬 自知综合评估报告</h1>
  <div class="meta">
    <span>📅 {period_label}</span>
    <span>📚 知识条目 {report_data['knowledge_total']}</span>
    <span>🪨 道痕 {report_data['daoben_total']}</span>
  </div>
  <div class="report-body">{report_html}</div>
  <div class="footer">由 Me · 自知 自动生成 | 基于知识库 + 道痕 + 历史报告综合分析</div>
</body></html>"""
    fname = f"review-{report_id}.html"
    file_path = REPORTS_DIR / fname
    file_path.write_text(html, encoding="utf-8")
    db.execute(
        "INSERT INTO reports(id,filename,created_at) VALUES(?,?,?)",
        [report_id, fname, datetime.now(timezone.utc).isoformat()]
    )
    db.commit()
    db.close()
    return {"ok": True, "message": "报告已生成", "report_id": report_id, "filename": fname}
