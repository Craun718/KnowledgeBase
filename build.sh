#!/bin/bash

# 构建和运行知识库应用的脚本

set -e

echo "开始构建知识库应用..."

# 构建Docker镜像
echo "正在构建Docker镜像..."
docker build -t knowledgebase:latest . --no-cache

echo "Docker镜像构建完成！"

# 询问是否要运行容器
read -p "是否要立即运行容器？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在启动容器..."
    docker-compose up -d
    
    echo "等待服务启动..."
    sleep 10
    
    echo "服务状态："
    docker-compose ps
    
    echo ""
    echo "应用已启动！"
    echo "前端地址: http://localhost:8010"
    echo "API文档: http://localhost:8010/docs"
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
fi