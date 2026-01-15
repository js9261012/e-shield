"""
結構化日誌配置
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os


def setup_logging():
    """
    設定結構化日誌
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # 設定根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level, logging.INFO))
    
    # 清除現有的 handlers
    root_logger.handlers.clear()
    
    # 建立格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台輸出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 檔案輸出（可選）
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 設定第三方庫的日誌級別
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return root_logger
