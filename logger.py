"""
Logging Module for Smart Attendance System v2
Provides structured logging with rotation
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import config


class Logger:
    """Centralized logging for the application"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        logger = logging.getLogger('attendance_system')
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler with rotation
        try:
            file_handler = RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=config.LOG_MAX_SIZE,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create log file: {e}")
        
        return logger
    
    @property
    def logger(self):
        """Get the logger instance"""
        return self._logger
    
    def debug(self, message):
        self._logger.debug(message)
    
    def info(self, message):
        self._logger.info(message)
    
    def warning(self, message):
        self._logger.warning(message)
    
    def error(self, message):
        self._logger.error(message)
    
    def critical(self, message):
        self._logger.critical(message)
    
    def exception(self, message):
        self._logger.exception(message)


# Global logger instance
logger = Logger()


def get_logger():
    """Get the global logger instance"""
    return logger
