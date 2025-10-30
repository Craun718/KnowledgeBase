# 阶段1: 构建前端
FROM node:20-slim AS frontend-builder

# 镜像元数据
LABEL maintainer="ProblemPrincipal <3653544699@qq.com>"
LABEL version="1.0.0"
LABEL description="Prevention of Marine Disasters Knowledge Base application with FastAPI backend and React frontend"
LABEL org.opencontainers.image.title="Prevention of Marine Disasters Knowledge Base"
LABEL org.opencontainers.image.description="A full-stack knowledge base application with AI-powered search capabilities"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="ProblemPrincipal"
LABEL org.opencontainers.image.vendor="AI Competition"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="2025-10-30"

# 设置工作目录
WORKDIR /app/frontend

# 安装 pnpm
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g pnpm && \
    pnpm config set registry https://registry.npmmirror.com

# 复制前端依赖文件
COPY kb-frontend/package.json kb-frontend/pnpm-lock.yaml ./

# 安装前端依赖
RUN pnpm install --frozen-lockfile

# 复制前端源代码
COPY kb-frontend/ ./

# 构建前端
RUN pnpm run build

# 阶段2: 准备Python环境和后端
FROM python:3.12-slim AS backend-base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --upgrade pip

# 设置工作目录
WORKDIR /app

# 复制Python依赖文件
COPY pyproject.toml ./

# 安装Python依赖
RUN pip install -e .

# 阶段3: 最终镜像
FROM python:3.12-slim AS production

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从backend-base阶段复制Python环境
COPY --from=backend-base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-base /usr/local/bin /usr/local/bin

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY . .

# 从frontend-builder阶段复制构建好的前端文件
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# 配置nginx
COPY nginx.conf /etc/nginx/sites-available/default

# 配置supervisor
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

# 创建必要的目录
RUN mkdir -p /var/log/nginx /app/logs /app/data /app/tmp/cache /app/chroma_db

# 设置权限
RUN chown -R www-data:www-data /var/www/html

# 暴露端口
EXPOSE 8010

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/ || exit 1

# 启动命令
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]