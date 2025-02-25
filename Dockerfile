# 使用官方 Python 运行时作为父镜像
FROM python:3.11-alpine
WORKDIR /app
COPY . /app/
RUN apk add --no-cache sqlite
RUN pip install --no-cache-dir -r requirements.txt

# 设置默认命令
CMD ["gunicorn", "--workers=1", "--bind=0.0.0.0:5000", "--reload", "app.app:app"]