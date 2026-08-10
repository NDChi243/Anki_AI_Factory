"""
📋 Logger Module — Hệ thống logging tập trung cho AnkiTool

Thay thế tất cả print() statements bằng logging.
Log đồng thời ra file và console (Anki debug window).
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Singleton logger
_logger: logging.Logger | None = None
_initialized: bool = False

# Đường dẫn file log
_LOG_FILENAME = "anki_tool.log"
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_LOG_BACKUP_COUNT = 3  # Giữ 3 file log cũ


def _get_log_dir() -> str:
    """Lấy thư mục chứa file log (cùng thư mục với addon)"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_logging(level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True) -> logging.Logger:
    """
    Khởi tạo logger cho toàn bộ add-on.
    Chỉ cần gọi 1 lần khi add-on khởi động.

    Args:
        level: Mức log ("DEBUG", "INFO", "WARNING", "ERROR")
        log_to_file: Ghi log ra file
        log_to_console: Ghi log ra console (Anki stdout)

    Returns:
        Logger instance
    """
    global _logger, _initialized

    if _initialized and _logger is not None:
        return _logger

    _logger = logging.getLogger("AnkiTool")
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    _logger.handlers.clear()

    # Format
    fmt = logging.Formatter(
        "[AnkiTool] %(asctime)s [%(levelname)-7s] %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (có rotation)
    if log_to_file:
        try:
            file_handler = RotatingFileHandler(
                os.path.join(_get_log_dir(), _LOG_FILENAME),
                maxBytes=_LOG_MAX_BYTES,
                backupCount=_LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            _logger.addHandler(file_handler)
        except Exception:
            pass  # Fallback: không ghi file cũng được

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        # Format ngắn hơn cho console
        console_fmt = logging.Formatter(
            "[AnkiTool] %(levelname)-7s | %(message)s"
        )
        console_handler.setFormatter(console_fmt)
        _logger.addHandler(console_handler)

    _initialized = True
    _logger.info("Logger initialized (level=%s)", level)
    return _logger


def get_logger() -> logging.Logger:
    """Lấy logger instance. Tự động gọi setup_logging() nếu chưa khởi tạo."""
    global _logger
    if _logger is None:
        return setup_logging()
    return _logger


# Convenience functions
def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """Log error + traceback"""
    get_logger().exception(msg, *args, **kwargs)
