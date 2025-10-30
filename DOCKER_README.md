# Docker 部署指南

本项目使用 Docker 多阶段构建，基于 Debian 将 FastAPI 后端和前端打包到一个镜像中。

## 架构说明

- **基础镜像**: Debian bookworm-slim
- **前端**: React + Rsbuild，构建后的静态文件由 Nginx 提供服务
- **后端**: FastAPI + Python 3，通过 uVicorn 运行
- **反向代理**: Nginx 处理静态文件和 API 代理
- **进程管理**: Supervisor 管理 Nginx 和 FastAPI 进程

## 快速开始

### 方法1: 使用构建脚本

**Windows:**
```bash
.\build.bat
```

**Linux/Mac:**
```bash
chmod +x build.sh
./build.sh
```

### 方法2: 使用 Docker Compose

```bash
# 构建并启动
docker-compose up --build -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法3: 直接使用 Docker

```bash
# 构建镜像
docker build -t knowledgebase:latest .

# 运行容器
docker run -d \
  --name kb-app \
  -p 80:80 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/chroma_db:/app/chroma_db \
  knowledgebase:latest
```

## 访问地址

- **前端应用**: http://localhost
- **API 文档**: http://localhost/docs
- **ReDoc 文档**: http://localhost/redoc

## 目录结构

```
/app/                   # 应用根目录
├── main.py            # FastAPI 入口
├── routes/            # API 路由
├── service/           # 业务逻辑
├── utils/             # 工具函数
├── data/              # 数据文件 (挂载卷)
├── logs/              # 日志文件 (挂载卷)
├── chroma_db/         # 数据库文件 (挂载卷)
└── models/            # 模型文件 (挂载卷)

/var/www/html/         # 前端静态文件
```

## 数据持久化

以下目录建议挂载为卷以实现数据持久化：

- `./data:/app/data` - 上传的文件和数据
- `./logs:/app/logs` - 应用日志
- `./chroma_db:/app/chroma_db` - ChromaDB 数据库文件
- `./models:/app/models` - AI 模型文件

## 环境变量

可以通过环境变量配置应用：

```bash
docker run -d \
  -e PYTHONUNBUFFERED=1 \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  knowledgebase:latest
```

## 健康检查

容器包含健康检查机制：
- 检查间隔: 30秒
- 超时时间: 3秒
- 重试次数: 3次
- 启动期间: 5秒

## 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f kb-app

# 查看容器内部日志
docker exec -it kb-app tail -f /var/log/fastapi.log
docker exec -it kb-app tail -f /var/log/nginx/access.log
```

## 故障排除

### 1. 容器启动失败
```bash
# 查看容器日志
docker logs kb-app

# 进入容器调试
docker exec -it kb-app /bin/bash
```

### 2. 前端无法访问
检查 Nginx 配置和静态文件是否正确部署：
```bash
docker exec -it kb-app ls -la /var/www/html/
docker exec -it kb-app nginx -t
```

### 3. API 无法访问
检查 FastAPI 服务状态：
```bash
docker exec -it kb-app curl http://localhost:8000/docs
docker exec -it kb-app supervisorctl status
```

## 开发模式

如果需要开发模式，可以创建 `docker-compose.dev.yml`：

```yaml
version: '3.8'
services:
  kb-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"  # 直接暴露FastAPI端口
    volumes:
      - .:/app       # 挂载源代码
    command: python main.py  # 直接运行FastAPI
```

## 性能优化

1. **多阶段构建**: 减少最终镜像大小
2. **依赖缓存**: 优化 Docker 构建缓存
3. **静态文件**: Nginx 直接提供静态文件服务
4. **进程管理**: Supervisor 确保服务稳定运行

## 安全考虑

1. 使用非 root 用户运行应用（可选配置）
2. 定期更新基础镜像
3. 扫描镜像漏洞
4. 配置适当的网络策略