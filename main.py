from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger as log
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from routes.file import router as file_router
from routes.swaggerui import setupSwaggerUI

from log import log_init

log_init()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before the application starts
    log.info("FastAPI application is starting up...")
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

setupSwaggerUI(app)

app.include_router(file_router, tags=["文件管理"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
