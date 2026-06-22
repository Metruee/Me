from __future__ import annotations
"""
Export API（数据导出）
"""
import io
import json
import logging
import zipfile
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.config import DB_PATH, REPORTS_DIR
from core.db import get_db

logger = logging.getLogger("me-backend")
router = APIRouter()


@router.get("/export")
def export_data():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if DB_PATH.exists():
            zf.writestr("me.db", DB_PATH.read_bytes())
        if REPORTS_DIR.exists():
            for f in REPORTS_DIR.rglob("*.html"):
                zf.write(f, f"reports/{f.name}")
        db = get_db()
        rows = db.execute("SELECT * FROM knowledge_entries").fetchall()
        zf.writestr("knowledge_export.json", json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        daoben_rows = db.execute("SELECT * FROM daoben_entries").fetchall()
        zf.writestr("daoben_export.json", json.dumps([dict(r) for r in daoben_rows], ensure_ascii=False, indent=2))
        # 导出记忆数据
        imp_rows = db.execute("SELECT * FROM impressions").fetchall()
        zf.writestr("impressions_export.json", json.dumps([dict(r) for r in imp_rows], ensure_ascii=False, indent=2))
        evt_rows = db.execute("SELECT * FROM event_records").fetchall()
        zf.writestr("events_export.json", json.dumps([dict(r) for r in evt_rows], ensure_ascii=False, indent=2))
        db.close()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=me-export-{datetime.now().strftime('%Y%m%d')}.zip"
        },
    )
