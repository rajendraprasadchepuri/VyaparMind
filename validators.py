"""
Centralized Validation Module for VyaparMind

This module provides validation functions for business rules, data formats,
and integrity constraints across the application.
"""

import re
from datetime import datetime, date
from typing import Any, Optional, Tuple
from exceptions import (
    ValidationError, BusinessRuleError, StockError,
    InsufficientStockError, NegativeStockError, PricingError
)


# ==================== FORMAT VALIDATORS ====================

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format (Indian format).
    
    Args:
        phone: Phone number to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"
    
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check for 10-digit Indian number or international format
    if not re.match(r'^(\+91)?[6-9]\d{9}$', cleaned):
        return False, "Invalid phone number format (expected 10 digits starting with 6-9)"
    
    return True, ""


def validate_pincode(pincode: str) -> Tuple[bool, str]:
    """
    Validate Indian pincode format.
    
    Args:
        pincode: Pincode to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pincode:
        return False, "Pincode is required"
    
    if not re.match(r'^\d{6}$', pincode):
        return False, "Invalid pincode format (expected 6 digits)"
    
    return True, ""


def validate_id_format(id_value: str, prefix: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate ID format.
    
    Args:
        id_value: ID to validate
        prefix: Optional expected prefix
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not id_value:
        return False, "ID is required"
    
    if prefix and not id_value.startswith(prefix):
        return False, f"ID must start with '{prefix}'"
    
    # Check for alphanumeric
    if not re.match(r'^[A-Za-z0-9_-]+$', id_value):
        return False, "ID must contain only alphanumeric characters, hyphens, and underscores"
    
    return True, ""


# ==================== BUSINESS RULE VALIDATORS ====================

def validate_stock_quantity(quantity: Any, allow_zero: bool = True) -> Tuple[bool, str]:
    """
    Validate stock quantity.
    
    Args:
        quantity: Stock quantity to validate
        allow_zero: Whether to allow zero stock
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        qty = int(quantity)
    except (ValueError, TypeError):
        return False, "Stock quantity must be a valid number"
    
    if qty < 0:
        return False, "Stock quantity cannot be negative"
    
    if not allow_zero and qty == 0:
        return False, "Stock quantity must be greater than zero"
    
    return True, ""


def validate_price(price: Any, allow_zero: bool = False) -> Tuple[bool, str]:
    """
    Validate price value.
    
    Args:
        price: Price to validate
        allow_zero: Whether to allow zero price
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        price_val = float(price)
    except (ValueError, TypeError):
        return False, "Price must be a valid number"
    
    if price_val < 0:
        return False, "Price cannot be negative"
    
    if not allow_zero and price_val == 0:
        return False, "Price must be greater than zero"
    
    # Check for reasonable maximum (10 million)
    if price_val > 10_000_000:
        return False, "Price exceeds maximum allowed value"
    
    return True, ""


def validate_cost_vs_price(cost: float, price: float, allow_loss: bool = False) -> Tuple[bool, str]:
    """
    Validate cost price vs selling price.
    
    Args:
        cost: Cost price
        price: Selling price
        allow_loss: Whether to allow selling at a loss
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not allow_loss and price < cost:
        return False, f"Selling price (₹{price}) is less than cost price (₹{cost})"
    
    return True, ""


def validate_tax_rate(tax_rate: Any) -> Tuple[bool, str]:
    """
    Validate tax rate.
    
    Args:
        tax_rate: Tax rate to validate (as percentage)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        rate = float(tax_rate)
    except (ValueError, TypeError):
        return False, "Tax rate must be a valid number"
    
    if rate < 0:
        return False, "Tax rate cannot be negative"
    
    if rate > 100:
        return False, "Tax rate cannot exceed 100%"
    
    return True, ""


def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> Tuple[bool, str]:
    """
    Validate date format.
    
    Args:
        date_str: Date string to validate
        format: Expected date format
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date is required"
    
    try:
        datetime.strptime(date_str, format)
        return True, ""
    except ValueError:
        return False, f"Invalid date format (expected {format})"


def validate_expiry_date(expiry_date: str) -> Tuple[bool, str]:
    """
    Validate expiry date (must be in future).
    
    Args:
        expiry_date: Expiry date string (YYYY-MM-DD)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, msg = validate_date_format(expiry_date)
    if not is_valid:
        return False, msg
    
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        today = date.today()
        
        if expiry < today:
            return False, "Expiry date cannot be in the past"
        
        return True, ""
    except ValueError:
        return False, "Invalid expiry date"


def validate_discount_percentage(discount: Any) -> Tuple[bool, str]:
    """
    Validate discount percentage.
    
    Args:
        discount: Discount percentage to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        disc = float(discount)
    except (ValueError, TypeError):
        return False, "Discount must be a valid number"
    
    if disc < 0:
        return False, "Discount cannot be negative"
    
    if disc > 100:
        return False, "Discount cannot exceed 100%"
    
    return True, ""


def validate_quantity_available(requested: int, available: int, product_name: str = "") -> Tuple[bool, str]:
    """
    Validate that requested quantity is available.
    
    Args:
        requested: Requested quantity
        available: Available quantity
        product_name: Product name for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if requested > available:
        product_info = f" for {product_name}" if product_name else ""
        return False, f"Insufficient stock{product_info}. Requested: {requested}, Available: {available}"
    
    return True, ""


# ==================== MULTI-TENANT VALIDATORS ====================

def validate_account_id(account_id: str) -> Tuple[bool, str]:
    """
    Validate account ID format.
    
    Args:
        account_id: Account ID to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not account_id:
        return False, "Account ID is required"
    
    # Check length (should be 16 characters for generated IDs)
    if len(account_id) < 8:
        return False, "Account ID too short"
    
    # Check for alphanumeric
    if not re.match(r'^[A-Za-z0-9]+$', account_id):
        return False, "Account ID must be alphanumeric"
    
    return True, ""


def validate_isolation(resource_account_id: str, user_account_id: str, resource_type: str = "resource") -> Tuple[bool, str]:
    """
    Validate multi-tenant isolation.
    
    Args:
        resource_account_id: Account ID of the resource
        user_account_id: Account ID of the user
        resource_type: Type of resource for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if resource_account_id != user_account_id:
        return False, f"Access denied: {resource_type} belongs to different account"
    
    return True, ""


# ==================== UTILITY FUNCTIONS ====================

def validate_required_fields(data: dict, required_fields: list) -> Tuple[bool, str]:
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of required field names
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing.append(field)
    
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    return True, ""


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\"\'%;()&+]', '', str(value))
    
    # Trim to max length
    return sanitized[:max_length].strip()


def validate_and_raise(is_valid: bool, error_message: str, exception_class=ValidationError):
    """
    Helper to validate and raise exception if invalid.
    
    Args:
        is_valid: Validation result
        error_message: Error message if invalid
        exception_class: Exception class to raise
    
    Raises:
        exception_class if is_valid is False
    """
    if not is_valid:
        raise exception_class(error_message)
