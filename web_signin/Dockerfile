FROM python:3.12-slim

# 基础环境设置
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 将整个仓库拷贝进容器，方便复用根目录下的 utils、auto_add_user 等模块
COPY . /app

# 安装 Web 版所需依赖
RUN pip install --upgrade pip && \
    pip install -r web_signin/requirements.txt

# 默认暴露端口（实际端口仍由 config.json / WEB_SIGNIN_PORT 决定，compose 已默认改为 9988）
EXPOSE 9988

# 容器启动命令
CMD ["python", "web_signin/run.py"]

