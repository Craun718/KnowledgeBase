from contextlib import asynccontextmanager
import asyncio
from loguru import logger as log
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.swaggerui import setupSwaggerUI
from routes.file import router as file_router
from routes.search import router as search_router

from log import log_init

from load_pdf import load_all_pdfs

log_init()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init_embedding_db()
    log.info("FastAPI application is starting up...")
    # 在应用对外可用之前，先在后台线程执行 PDF 加载与入库操作
    try:
        # await asyncio.get_running_loop().run_in_executor(None, load_all_pdfs)
        log.info("load_pdf completed before FastAPI startup.")
    except Exception as e:
        log.exception("Error while running load_all_pdfs before startup: {}", e)
    yield
    # after the application stops
    log.info("FastAPI application is shutting down.")
    pass


app = FastAPI(
    title="KB API",
    version="1.0.0",
    description="",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


setupSwaggerUI(app)

app.include_router(file_router, tags=["文件管理"])
app.include_router(search_router, tags=["知识检索"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
