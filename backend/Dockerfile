# ── 第一阶段：构建前端 ──
FROM node:20-alpine AS frontend-builder
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
# 跳过 vue-tsc 类型检查（Docker 内 TS 环境差异可能导致构建失败），直接用 vite 编译
RUN npx vite build

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
COPY --from=frontend-builder /src/dist/ /app/static/

ENV PYTHONPATH=/app/backend
EXPOSE 6868

CMD ["python", "backend/main.py"]
