import logging
import sys
from datetime import datetime

from loguru import logger as log
from config import self_dir


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # 获取Loguru对应的日志级别
        try:
            level = log.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者的信息
        frame, depth = logging.currentframe(), 2
        while frame and (
            frame.f_code.co_filename.endswith("logging\\__init__.py")
            or frame.f_code.co_filename.endswith("log.py")
        ):
            frame = frame.f_back
            depth += 1

        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def log_init():
    # Remove any existing handlers to avoid duplication
    log.remove()

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = [InterceptHandler()]

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = [InterceptHandler()]

    log_dir = self_dir.joinpath("logs")
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir.joinpath("info").joinpath(
        f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )
    log_path.parent.mkdir(exist_ok=True)

    log.add(
        log_path,
        rotation="1 MB",
        level="INFO",
        retention="1 months",
        serialize=True,
    )

    # Always log to stdout with a specific format
    log.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{file: >10}</cyan>:<cyan>{line: <3}</cyan> | <cyan>{function}</cyan> | <level>{message}</level>",
    )

    log.info("Starting application...")
    log.info(f"Logging to file: {log_path}")
