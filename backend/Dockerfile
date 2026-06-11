FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# 前端静态文件（Vue build 产物）
COPY frontend/dist/ /app/static/

EXPOSE 6868

CMD ["python", "main.py"]
