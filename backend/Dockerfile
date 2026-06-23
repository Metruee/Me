# ── 第二阶段：运行环境 ──
FROM python:3.11-slim

WORKDIR /app

# Python 依赖
COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-chi-sim && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# 后端源码
COPY backend/ ./backend/
RUN mkdir -p /app/backend

# 前端构建产物（从第一阶段复制）
COPY backend/static/ /app/static/

ENV PYTHONPATH=/app/backend
EXPOSE 6868

CMD ["python", "backend/main.py"]
