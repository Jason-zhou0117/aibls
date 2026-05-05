# 1. 基础镜像：使用 Python 3.10 的轻量版
FROM python:3.10-slim

# 2. 设置工作目录：容器内的操作都在这个目录下
WORKDIR /app

# 3. 设置环境变量：配置 Python 行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4. 复制依赖文件（先复制 requirements.txt，利用 Docker 缓存）
COPY requirements.txt .

# 5. 安装 Python 依赖
RUN pip install -r requirements.txt

# 6. 复制项目代码
COPY aibls ./aibls
COPY web ./web
COPY app.py .
COPY bili_mon.db .

# 7. 创建日志目录
RUN mkdir -p /app/logs

# 8. 声明容器要用的端口
EXPOSE 5001

# 9. 启动命令
CMD ["python", "app.py"]