FROM python:3.11-slim

WORKDIR /app

# Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 后端源码
COPY backend/main.py .

# 前端构建产物（需要在容器外先执行 npm run build）
COPY frontend/dist/ /app/static/

EXPOSE 6868

CMD ["python", "main.py"]
