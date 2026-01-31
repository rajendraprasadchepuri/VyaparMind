"""
Custom Exception Classes for VyaparMind Application

This module defines specific exception types for better error handling,
debugging, and user feedback across the application.
"""


class VyaparMindException(Exception):
    """Base exception class for all VyaparMind errors."""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class DatabaseError(VyaparMindException):
    """Raised when database operations fail."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when a database query fails."""
    pass


class TransactionError(DatabaseError):
    """Raised when a database transaction fails or needs rollback."""
    pass


class ValidationError(VyaparMindException):
    """Raised when data validation fails."""
    pass


class BusinessRuleError(ValidationError):
    """Raised when business logic rules are violated."""
    pass


class IsolationError(VyaparMindException):
    """Raised when multi-tenant isolation is violated."""
    pass


class AuthenticationError(VyaparMindException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(VyaparMindException):
    """Raised when user lacks required permissions."""
    pass


class StockError(BusinessRuleError):
    """Raised when stock-related operations fail."""
    pass


class InsufficientStockError(StockError):
    """Raised when attempting to sell more stock than available."""
    pass


class NegativeStockError(StockError):
    """Raised when stock quantity would become negative."""
    pass


class PricingError(BusinessRuleError):
    """Raised when pricing rules are violated."""
    pass


class TransactionProcessingError(VyaparMindException):
    """Raised when transaction processing fails."""
    pass


class ExternalServiceError(VyaparMindException):
    """Raised when external service calls fail (email, WhatsApp, etc.)."""
    pass


class ConfigurationError(VyaparMindException):
    """Raised when configuration is invalid or missing."""
    pass


class DataIntegrityError(DatabaseError):
    """Raised when data integrity constraints are violated."""
    pass


# Error code mappings for structured error responses
ERROR_CODES = {
    'DB_CONNECTION_FAILED': 'Database connection failed',
    'DB_QUERY_FAILED': 'Database query execution failed',
    'DB_TRANSACTION_FAILED': 'Database transaction failed',
    'VALIDATION_FAILED': 'Data validation failed',
    'BUSINESS_RULE_VIOLATED': 'Business rule violation',
    'ISOLATION_VIOLATED': 'Multi-tenant isolation violated',
    'AUTH_FAILED': 'Authentication failed',
    'AUTHZ_FAILED': 'Authorization failed',
    'INSUFFICIENT_STOCK': 'Insufficient stock available',
    'NEGATIVE_STOCK': 'Stock cannot be negative',
    'INVALID_PRICE': 'Invalid price value',
    'TRANSACTION_FAILED': 'Transaction processing failed',
    'EXTERNAL_SERVICE_FAILED': 'External service call failed',
    'CONFIG_ERROR': 'Configuration error',
    'DATA_INTEGRITY_ERROR': 'Data integrity constraint violated',
}


def get_error_message(error_code, **kwargs):
    """
    Get a formatted error message for a given error code.
    
    Args:
        error_code: Error code from ERROR_CODES
        **kwargs: Additional context to include in the message
    
    Returns:
        Formatted error message string
    """
    base_message = ERROR_CODES.get(error_code, 'Unknown error')
    if kwargs:
        context = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        return f"{base_message} ({context})"
    return base_message
