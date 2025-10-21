"""
Helper utilities for the bot
General-purpose utility functions
"""
import re
from datetime import datetime

def truncate_text(text, max_length=640, suffix="..."):
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_currency(amount, currency="₱"):
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        str: Formatted currency string
    """
    return f"{currency}{amount:,.2f}"

def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """
    Validate Philippine phone number
    
    Args:
        phone: Phone number string
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces and dashes
    phone = re.sub(r'[\s-]', '', phone)
    
    # Check for valid Philippine formats
    # +639xxxxxxxxx, 09xxxxxxxxx, 639xxxxxxxxx
    patterns = [
        r'^\+639\d{9}$',
        r'^09\d{9}$',
        r'^639\d{9}$'
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)

def format_timestamp(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format datetime as string
    
    Args:
        dt: Datetime object (defaults to now)
        format_str: Format string
    
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

def clean_text(text):
    """
    Clean and sanitize text input
    
    Args:
        text: Text to clean
    
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove potential harmful characters
    text = text.replace('<', '').replace('>', '')
    
    return text.strip()

def generate_button_title(text, max_length=20):
    """
    Generate button title with proper truncation
    
    Args:
        text: Original text
        max_length: Maximum button title length
    
    Returns:
        str: Truncated button title
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 1] + "…"
