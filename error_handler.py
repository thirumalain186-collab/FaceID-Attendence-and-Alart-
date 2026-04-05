"""
Custom Exception Classes for Smart Attendance System v2
Provides clear, maintainable error handling throughout the application
"""

from logger import get_logger

logger = get_logger()


class AttendanceException(Exception):
    """Base exception for attendance-related errors"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        logger.error(f"AttendanceException: {message} | Details: {self.details}")
        super().__init__(self.message)


class DatabaseException(AttendanceException):
    """Exception for database operation failures"""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        self.operation = operation
        full_details = details or {}
        if operation:
            full_details['operation'] = operation
        super().__init__(f"Database error: {message}", full_details)


class EmailException(AttendanceException):
    """Exception for email sending failures"""
    
    def __init__(self, message: str, recipient: str = None, details: dict = None):
        self.recipient = recipient
        full_details = details or {}
        if recipient:
            full_details['recipient'] = recipient
        super().__init__(f"Email error: {message}", full_details)


class CameraException(AttendanceException):
    """Exception for camera access or operation failures"""
    
    def __init__(self, message: str, camera_index: int = None, details: dict = None):
        self.camera_index = camera_index
        full_details = details or {}
        if camera_index is not None:
            full_details['camera_index'] = camera_index
        super().__init__(f"Camera error: {message}", full_details)


class RecognitionException(AttendanceException):
    """Exception for face recognition failures"""
    
    def __init__(self, message: str, confidence: float = None, details: dict = None):
        self.confidence = confidence
        full_details = details or {}
        if confidence is not None:
            full_details['confidence'] = confidence
        super().__init__(f"Recognition error: {message}", full_details)


class ConfigurationException(AttendanceException):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        self.config_key = config_key
        full_details = details or {}
        if config_key:
            full_details['config_key'] = config_key
        super().__init__(f"Configuration error: {message}", full_details)


class TrainingException(AttendanceException):
    """Exception for model training failures"""
    
    def __init__(self, message: str, person_name: str = None, details: dict = None):
        self.person_name = person_name
        full_details = details or {}
        if person_name:
            full_details['person_name'] = person_name
        super().__init__(f"Training error: {message}", full_details)


class SchedulerException(AttendanceException):
    """Exception for scheduler operation failures"""
    
    def __init__(self, message: str, job_id: str = None, details: dict = None):
        self.job_id = job_id
        full_details = details or {}
        if job_id:
            full_details['job_id'] = job_id
        super().__init__(f"Scheduler error: {message}", full_details)
