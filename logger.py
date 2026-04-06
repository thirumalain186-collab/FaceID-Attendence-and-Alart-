"""
Logging Module for Smart Attendance System v2
Provides structured logging with rotation
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logged_setup = False
_setup_lock = threading.Lock()


def _setup_logging():
    """Setup logging once at module level - thread-safe initialization."""
    global _logged_setup
    
    if _logged_setup:
        return
    
    with _setup_lock:
        if _logged_setup:
            return
        
        _log_level = logging.INFO
        _log_file = Path("logs") / "attendance.log"
        _log_max_size = 5242880
        _log_backup_count = 5
        _log_dir = Path("logs")
        
        try:
            import config as _cfg
            _log_level = getattr(logging, _cfg.LOG_LEVEL, logging.INFO)
            _log_file = _cfg.LOG_FILE
            _log_max_size = _cfg.LOG_MAX_SIZE
            _log_backup_count = _cfg.LOG_BACKUP_COUNT
            _log_dir = _cfg.LOGS_DIR
        except ImportError:
            pass
        except AttributeError:
            pass
        
        try:
            _log_dir.mkdir(exist_ok=True)
        except OSError:
            pass
        
        logger = logging.getLogger('attendance_system')
        logger.setLevel(_log_level)
        logger.propagate = False
        
        if logger.handlers:
            _logged_setup = True
            return
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        try:
            file_handler = RotatingFileHandler(
                str(_log_file),
                maxBytes=_log_max_size,
                backupCount=_log_backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError, PermissionError) as e:
            print(f"Warning: Could not create log file: {e}", file=sys.stderr)
        
        _logged_setup = True


def get_logger():
    """Get the global logger instance, initializing if needed."""
    _setup_logging()
    return logging.getLogger('attendance_system')


def reset_logger():
    """Reset the logger - removes all handlers. Useful for testing."""
    global _logged_setup
    _logged_setup = False
    logger = logging.getLogger('attendance_system')
    for handler in logger.handlers[:]:
        try:
            handler.close()
            logger.removeHandler(handler)
        except Exception:
            pass
    logger.setLevel(logging.INFO)
    logger.propagate = True
