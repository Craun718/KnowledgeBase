from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger as log
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from requests import RequestException
from requests.exceptions import HTTPError
from routes.swaggerui import setupSwaggerUI
from routes.file import router as file_router
from routes.search import router as search_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


setupSwaggerUI(app)

app.include_router(file_router, tags=["文件管理"])
app.include_router(search_router, tags=["知识检索"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
