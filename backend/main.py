"""
Me Backend — FastAPI

模块化架构（已拆分）：
  core/       配置、数据库、数据模型
  providers/  LLM / Embedding 提供者抽象
  memory/     三区记忆系统（印象/事件/经验）
  context/    Context Assembly 三级缓存
  tools/      工具注册与执行（ToolRegistry）
  routes/     API 路由模块
"""
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import ME_HOME, DB_PATH, REPORTS_DIR, STATIC_DIR, SKILLS_DIR
from core.db import get_db, init_db
from routes import (
    chat, sessions, archive, daoben, report, skills,
    settings, uploads, memory as memory_routes, export,
    config, models, experts,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("me-backend")

# ═══ App ═══════════════════════════════════════════════════
app = FastAPI(title="Me · 自知 API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══ Init ══════════════════════════════════════════════════
init_db()
# 启动时扫描 skills 目录，注册所有 SKILL.md 到 DB
from routes.skills import scan_skills
scan_skills()

# ═══ Routes ════════════════════════════════════════════════
app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(archive.router, prefix="/api")
app.include_router(daoben.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(memory_routes.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(experts.router, prefix="/api")

# ═══ 定时复盘调度器 ══════════════════════════════════════
_scheduler_stop = threading.Event()

def _do_scheduled_report(kind: str):
    from routes.report import _build_report_data, _generate_report_analysis, _markdown_to_html
    db = get_db()
    report_data = _build_report_data(db)
    if report_data["knowledge_total"] == 0 and report_data["daoben_total"] == 0:
        db.close()
        return
    report_md = _generate_report_analysis(report_data)
    report_html = _markdown_to_html(report_md)
    label = "周报" if kind == "weekly" else "月报"
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    period_label = f"{report_data['period_start'][:10]} ~ {report_data['period_end'][:10]}"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>Me · {label} {report_id}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width:800px; margin:0 auto; padding:40px 20px; color:#1c2e1c; background:#fafcfa; }}
  h1 {{ font-size:28px; border-bottom:2px solid #388e3c; padding-bottom:12px; }}
  h2 {{ font-size:20px; margin-top:32px; color:#388e3c; border-left:4px solid #388e3c; padding-left:12px; }}
  .report-body {{ line-height:1.9; }}
  .meta {{ font-size:13px; color:#8a9a8a; margin-bottom:24px; }}
  .footer {{ margin-top:40px; font-size:12px; color:#8a9a8a; border-top:1px solid #d8e4d8; padding-top:12px; }}
</style></head>
<body>
  <h1>🧬 自知{label}</h1>
  <div class="meta"><span>📅 {period_label}</span></div>
  <div class="report-body">{report_html}</div>
  <div class="footer">由 Me · 自知 自动生成</div>
</body></html>"""
    fname = f"{kind}-{report_id}.html"
    file_path = REPORTS_DIR / fname
    file_path.write_text(html, encoding="utf-8")
    db.execute(
        "INSERT INTO reports(id,filename,created_at) VALUES(?,?,?)",
        [report_id, fname, datetime.now(timezone.utc).isoformat()]
    )
    db.commit()
    db.close()

def _scheduler_loop():
    while not _scheduler_stop.wait(600):
        try:
            now = datetime.now()
            db = get_db()
            last = db.execute(
                "SELECT created_at, filename FROM reports ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            db.close()
            if now.weekday() == 6 and now.hour == 20 and now.minute < 10:
                needed = True
                if last:
                    last_dt = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
                    if last_dt.date() == now.date():
                        needed = False
                if needed:
                    _do_scheduled_report("weekly")
            if now.day == 1 and now.hour == 20 and now.minute < 10:
                needed = True
                if last:
                    last_dt = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
                    if last_dt.month == now.month and last_dt.year == now.year:
                        needed = False
                if needed:
                    _do_scheduled_report("monthly")
        except Exception:
            pass

_scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
_scheduler_thread.start()

# ═══ Static Files ══════════════════════════════════════════
if STATIC_DIR.exists():
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6868)
