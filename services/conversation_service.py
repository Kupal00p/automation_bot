"""
Conversation service module
Manages conversation state and order flow tracking
For production, use Redis for distributed state management
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory conversation state (use Redis in production)
# Structure: {user_id: {'state': 'awaiting_address', 'data': {...}, 'expires_at': timestamp}}
conversation_state = {}

# Order flow states
class OrderState:
    """Order flow state constants"""
    IDLE = "idle"
    AWAITING_QUANTITY = "awaiting_quantity"
    AWAITING_NAME = "awaiting_name"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_ADDRESS = "awaiting_address"
    AWAITING_PAYMENT_METHOD = "awaiting_payment_method"
    AWAITING_CONFIRMATION = "awaiting_confirmation"

# ================================================
# STATE MANAGEMENT
# ================================================
def set_conversation_state(user_id, state, data=None, ttl_minutes=30):
    """
    Set conversation state for a user
    
    Args:
        user_id: User's messenger ID
        state: Current state in the order flow
        data: Dictionary of order data
        ttl_minutes: Time to live in minutes
    """
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
    
    conversation_state[user_id] = {
        'state': state,
        'data': data or {},
        'expires_at': expires_at,
        'updated_at': datetime.now()
    }
    
    logger.info(f"🔄 Set state for {user_id}: {state}")

def get_conversation_state(user_id):
    """
    Get conversation state for a user
    
    Args:
        user_id: User's messenger ID
    
    Returns:
        dict: State dictionary or None if expired/not found
    """
    if user_id not in conversation_state:
        return None
    
    state_data = conversation_state[user_id]
    
    # Check if expired
    if datetime.now() > state_data['expires_at']:
        logger.warning(f"⚠️ State expired for {user_id}")
        clear_conversation_state(user_id)
        return None
    
    return state_data

def update_conversation_data(user_id, key, value):
    """
    Update specific data in conversation state
    
    Args:
        user_id: User's messenger ID
        key: Data key to update
        value: New value
    """
    if user_id in conversation_state:
        conversation_state[user_id]['data'][key] = value
        conversation_state[user_id]['updated_at'] = datetime.now()
        logger.info(f"📝 Updated {key} for {user_id}")

def clear_conversation_state(user_id):
    """
    Clear conversation state for a user
    
    Args:
        user_id: User's messenger ID
    """
    if user_id in conversation_state:
        del conversation_state[user_id]
        logger.info(f"🗑️ Cleared state for {user_id}")

def is_in_conversation(user_id):
    """
    Check if user is in an active conversation flow
    
    Args:
        user_id: User's messenger ID
    
    Returns:
        bool: True if in conversation, False otherwise
    """
    state = get_conversation_state(user_id)
    return state is not None and state['state'] != OrderState.IDLE

# ================================================
# ORDER DATA VALIDATION
# ================================================
def validate_phone_number(phone):
    """
    Validate Philippine phone number
    
    Args:
        phone: Phone number string
    
    Returns:
        tuple: (is_valid, formatted_phone or error_message)
    """
    import re
    
    # Remove spaces, dashes, and parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Philippine formats: +639xxxxxxxxx, 09xxxxxxxxx, 639xxxxxxxxx
    patterns = [
        (r'^\+639\d{9}$', lambda p: p),  # +639xxxxxxxxx
        (r'^09\d{9}$', lambda p: '+63' + p[1:]),  # 09xxxxxxxxx -> +639xxxxxxxxx
        (r'^639\d{9}$', lambda p: '+' + p),  # 639xxxxxxxxx -> +639xxxxxxxxx
    ]
    
    for pattern, formatter in patterns:
        if re.match(pattern, phone):
            return True, formatter(phone)
    
    return False, "Invalid phone number. Please use format: 09XXXXXXXXX or +639XXXXXXXXX"

def validate_quantity(quantity_text):
    """
    Validate quantity input
    
    Args:
        quantity_text: Quantity as string
    
    Returns:
        tuple: (is_valid, quantity or error_message)
    """
    try:
        quantity = int(quantity_text)
        if quantity < 1:
            return False, "Quantity must be at least 1"
        if quantity > 99:
            return False, "Maximum quantity is 99 per order"
        return True, quantity
    except ValueError:
        return False, "Please enter a valid number"

def validate_name(name):
    """
    Validate recipient name
    
    Args:
        name: Name string
    
    Returns:
        tuple: (is_valid, cleaned_name or error_message)
    """
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 255:
        return False, "Name is too long (max 255 characters)"
    
    # Clean and title case
    cleaned_name = ' '.join(name.strip().split())
    
    return True, cleaned_name

def validate_address(address):
    """
    Validate delivery address
    
    Args:
        address: Address string
    
    Returns:
        tuple: (is_valid, cleaned_address or error_message)
    """
    if not address or len(address.strip()) < 10:
        return False, "Please provide a complete address (minimum 10 characters)"
    
    if len(address) > 500:
        return False, "Address is too long (max 500 characters)"
    
    # Clean whitespace
    cleaned_address = ' '.join(address.strip().split())
    
    return True, cleaned_address

# ================================================
# CLEANUP (Run periodically)
# ================================================
def cleanup_expired_states():
    """
    Remove expired conversation states
    Should be called periodically (e.g., every hour)
    """
    now = datetime.now()
    expired_users = [
        user_id for user_id, state_data in conversation_state.items()
        if now > state_data['expires_at']
    ]
    
    for user_id in expired_users:
        del conversation_state[user_id]
    
    if expired_users:
        logger.info(f"🧹 Cleaned up {len(expired_users)} expired conversations")
    
    return len(expired_users)
