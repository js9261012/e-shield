"""
E-Shield 反爬蟲排隊系統 - FastAPI 主應用程式
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.api import health, products, queue, purchase
from app.services.product_service import ProductService
from app.tasks.queue_manager import start_queue_manager
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.logging import setup_logging
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("初始化商品資料...")
    ProductService.initialize_products()
    logger.info("啟動佇列管理任務...")
    start_queue_manager()
    logger.info("應用程式啟動完成")
    yield
    logger.info("應用程式關閉中...")


app = FastAPI(
    title="E-Shield 反爬蟲排隊系統",
    description="用於搶購稀有球鞋的反爬蟲排隊系統 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["健康檢查"])
app.include_router(products.router, prefix="/api", tags=["商品"])
app.include_router(queue.router, prefix="/api", tags=["佇列"])
app.include_router(purchase.router, prefix="/api", tags=["購買"])


@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "E-Shield 反爬蟲排隊系統 API",
        "version": "1.0.0",
        "docs": "/docs"
    }
