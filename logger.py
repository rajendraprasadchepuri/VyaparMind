"""
Centralized Logging System for VyaparMind

Provides structured logging with context, log levels, and rotation.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any


# Log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class ContextLogger:
    """Logger with contextual information."""
    
    def __init__(self, name: str = "vyaparmind"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup file and console handlers."""
        
        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, 'vyaparmind.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, 'errors.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _add_context(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Add contextual information to log message."""
        if context:
            context_str = json.dumps(context, default=str)
            return f"{message} | Context: {context_str}"
        return message
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.logger.debug(self._add_context(message, context))
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.logger.info(self._add_context(message, context))
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.logger.warning(self._add_context(message, context))
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message."""
        self.logger.error(self._add_context(message, context), exc_info=exc_info)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message."""
        self.logger.critical(self._add_context(message, context), exc_info=exc_info)
    
    def log_operation(self, operation: str, user: Optional[str] = None, 
                     account_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log an operation with standard context."""
        context = {
            'operation': operation,
            'timestamp': datetime.now().isoformat()
        }
        if user:
            context['user'] = user
        if account_id:
            context['account_id'] = account_id
        if details:
            context.update(details)
        
        self.info(f"Operation: {operation}", context)
    
    def log_error(self, error_type: str, error_message: str, 
                  user: Optional[str] = None, account_id: Optional[str] = None,
                  details: Optional[Dict] = None):
        """Log an error with standard context."""
        context = {
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        if user:
            context['user'] = user
        if account_id:
            context['account_id'] = account_id
        if details:
            context.update(details)
        
        self.error(f"Error: {error_type} - {error_message}", context, exc_info=True)


# Global logger instance
logger = ContextLogger()


# Convenience functions
def log_debug(message: str, **kwargs):
    """Log debug message."""
    logger.debug(message, kwargs if kwargs else None)


def log_info(message: str, **kwargs):
    """Log info message."""
    logger.info(message, kwargs if kwargs else None)


def log_warning(message: str, **kwargs):
    """Log warning message."""
    logger.warning(message, kwargs if kwargs else None)


def log_error(message: str, **kwargs):
    """Log error message."""
    exc_info = kwargs.pop('exc_info', False)
    logger.error(message, kwargs if kwargs else None, exc_info=exc_info)


def log_critical(message: str, **kwargs):
    """Log critical message."""
    exc_info = kwargs.pop('exc_info', False)
    logger.critical(message, kwargs if kwargs else None, exc_info=exc_info)


def log_operation(operation: str, user: Optional[str] = None, 
                 account_id: Optional[str] = None, **details):
    """Log an operation."""
    logger.log_operation(operation, user, account_id, details if details else None)


def log_db_error(error_message: str, query: Optional[str] = None, 
                 user: Optional[str] = None, account_id: Optional[str] = None):
    """Log database error."""
    details = {}
    if query:
        details['query'] = query[:200]  # Truncate long queries
    logger.log_error('DatabaseError', error_message, user, account_id, details)


def log_validation_error(error_message: str, field: Optional[str] = None,
                         value: Optional[Any] = None, user: Optional[str] = None):
    """Log validation error."""
    details = {}
    if field:
        details['field'] = field
    if value is not None:
        details['value'] = str(value)[:100]  # Truncate long values
    logger.log_error('ValidationError', error_message, user, None, details)


# Example usage:
if __name__ == "__main__":
    # Test logging
    log_info("Application started")
    log_operation("user_login", user="admin", account_id="TEST123", ip="192.168.1.1")
    log_warning("Low stock detected", product="Apple", stock=5)
    log_error("Database connection failed", exc_info=True, database="retail_supply_chain.db")
    log_db_error("Query timeout", query="SELECT * FROM products WHERE account_id = ?")
    log_validation_error("Invalid email format", field="email", value="invalid-email", user="test_user")
    
    print(f"\nLogs written to {LOG_DIR}/")
    print(f"  - vyaparmind.log (all logs)")
    print(f"  - errors.log (errors only)")
