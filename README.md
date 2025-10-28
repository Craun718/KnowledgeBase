# 知识库文件管理系统

这是一个基于FastAPI构建的简单知识库文件管理系统，提供文件上传、下载、列表查看和删除功能。

## 功能特点

- 文件上传：支持上传任意类型文件到知识库
- 文件列表：查看知识库中所有文件
- 文件下载：下载知识库中的指定文件
- 文件删除：从知识库中删除不需要的文件

## 安装与运行

### 环境要求

- Python 3.12 或更高版本

### 安装依赖

```bash
pip install -e .
```

或者使用uv：

```bash
uv sync
```

### 运行服务

```bash
python main.py
```

服务将在 http://localhost:8000 上启动。

## API文档

启动服务后，访问 http://localhost:8000/docs 可以查看自动生成的API文档。

### API端点

#### 上传文件

- **端点**: `POST /upload/file/`
- **参数**: file (UploadFile) - 要上传的文件
- **响应**: 上传成功信息

#### 获取文件列表

- **端点**: `GET /files/`
- **响应**: 文件名列表

#### 下载文件

- **端点**: `GET /download/{filename}`
- **参数**: filename (str) - 要下载的文件名
- **响应**: 文件内容

#### 删除文件

- **端点**: `DELETE /files/{filename}`
- **参数**: filename (str) - 要删除的文件名
- **响应**: 删除成功信息

## 项目结构

```
KnowledgeBase/
├── data/           # 存储上传的文件
│   └── files/      # 文件存储目录
├── main.py         # 主程序文件
├── pyproject.toml  # 项目配置文件
└── README.md       # 项目说明文档
```

## 使用示例

### 使用curl上传文件

```bash
curl -X POST "http://localhost:8000/upload/file/" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@example.txt"
```

### 使用curl获取文件列表

```bash
curl -X GET "http://localhost:8000/files/" -H "accept: application/json"
```

### 使用curl下载文件

```bash
curl -X GET "http://localhost:8000/download/example.txt" -H "accept: application/octet-stream" -o downloaded_file.txt
```

### 使用curl删除文件

```bash
curl -X DELETE "http://localhost:8000/files/example.txt" -H "accept: application/json"
```