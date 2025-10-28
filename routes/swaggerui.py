from pathlib import Path

from fastapi import BackgroundTasks
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import RedirectResponse, FileResponse
import httpx
from loguru import logger as log

STATIC_DIR = Path("./assets/static/")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

STATIC_FILES = {
    "swagger-ui-bundle.js": "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.27.0/swagger-ui-bundle.min.js",
    "swagger-ui.css": "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.27.0/swagger-ui.min.css",
    "redoc.standalone.js": "https://cdn-js.moeworld.top/npm/redoc@2/bundles/redoc.standalone.js",
}

# 跟踪正在下载的文件，避免重复下载
downloading_files = set()


async def download_file_async(url, file_path):
    """异步从URL下载文件并保存到本地"""
    try:
        # 标记为正在下载
        downloading_files.add(file_path.name)

        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()  # 如果请求失败，抛出异常
        content = response.read()
        # 保存文件到本地
        with open(file_path, "wb") as f:
            f.write(content)
        log.info(f"Successfully downloaded {file_path.name} to local")
        return True
    except Exception as e:
        log.error(f"Failed to download {file_path.name} from {url}: {e}")
        return False
    finally:
        # 移除下载标记
        if file_path.name in downloading_files:
            downloading_files.remove(file_path.name)


async def get_static_file(file_name: str, background_tasks: BackgroundTasks):
    """获取静态文件，如果本地没有则启动后台下载并立即返回重定向"""
    file_path = STATIC_DIR.joinpath(file_name)

    # 检查本地是否存在该文件
    if file_path.exists():
        return FileResponse(file_path)

    # 文件不存在，检查是否需要下载
    cdn_url = STATIC_FILES[file_name]
    if cdn_url and file_name not in downloading_files:
        # 将下载任务添加到后台，不等待完成
        background_tasks.add_task(download_file_async, cdn_url, file_path)
        log.warning(f"Started background download for {file_name}")

    # 立即返回重定向，不等下载完成
    return RedirectResponse(url=cdn_url)


def setupSwaggerUI(app):
    # Swagger UI静态文件重定向
    @app.get("/static/swagger-ui-bundle.js", include_in_schema=False)
    async def get_swagger_bundle(background_tasks: BackgroundTasks):
        return await get_static_file("swagger-ui-bundle.js", background_tasks)

    @app.get("/static/swagger-ui.css", include_in_schema=False)
    async def redirect_swagger_css(background_tasks: BackgroundTasks):
        return await get_static_file("swagger-ui.css", background_tasks)

    @app.get("/static/redoc.standalone.js", include_in_schema=False)
    async def redirect_redoc_standalone(background_tasks: BackgroundTasks):
        return await get_static_file("redoc.standalone.js", background_tasks)

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,  # type: ignore
            title="Custom Swagger UI",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)  # type: ignore
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,  # type: ignore
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )
