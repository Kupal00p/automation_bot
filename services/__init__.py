"""
Services package
Contains all business logic and service layer modules for the QuickSell bot
"""

# Database service
from .db_service import (
    get_db_connection,
    get_or_create_user,
    log_chat,
    get_keyword_reply
)

# Messenger service
from .messenger_service import (
    send_message,
    send_image,
    send_button_template,
    send_typing_indicator,
    mark_seen
)

# Handlers service
from .handlers_service import (
    handle_user_message,
    handle_postback,
    send_auto_greeting,
    send_main_menu
)

# Product service
from .product_service import (
    get_categories,
    show_categories,
    show_products_page,
    show_product_details,
    show_promos,
    show_shipping_info,
    user_pagination
)

# Order service
from .order_service import (
    handle_order_request,
    process_quantity_input,
    process_name_input,
    process_phone_input,
    process_address_input,
    process_payment_method,
    confirm_and_create_order,
    cancel_order,
    generate_order_number
)

# Conversation service
from .conversation_service import (
    set_conversation_state,
    get_conversation_state,
    update_conversation_data,
    clear_conversation_state,
    is_in_conversation,
    OrderState,
    validate_phone_number,
    validate_quantity,
    validate_name,
    validate_address
)

# Notification service
from .notification_service import (
    notify_new_order,
    notify_low_stock,
    notify_order_cancelled,
    notify_payment_received,
    notify_admins_messenger
)

# Admin service
from .admin_service import (
    get_all_orders,
    get_order_by_id,
    get_order_by_number,
    update_order_status,
    confirm_order_by_admin,
    cancel_order_by_admin,
    get_dashboard_stats,
    get_recent_activity,
    notify_customer_order_confirmed,
    notify_customer_order_cancelled,
    notify_customer_status_change
)

# Verification service
from .verification_service import (
    check_verification_required,
    initiate_verification,
    start_id_verification,
    start_upfront_payment,
    handle_id_upload,
    handle_selfie_upload,
    handle_payment_proof,
    approve_verification,
    reject_verification,
    is_trusted_buyer
)

__all__ = [
    # Database
    'get_db_connection',
    'get_or_create_user',
    'log_chat',
    'get_keyword_reply',
    
    # Messenger
    'send_message',
    'send_image',
    'send_button_template',
    'send_typing_indicator',
    'mark_seen',
    
    # Handlers
    'handle_user_message',
    'handle_postback',
    'send_auto_greeting',
    'send_main_menu',
    
    # Products
    'get_categories',
    'show_categories',
    'show_products_page',
    'show_product_details',
    'show_promos',
    'show_shipping_info',
    'user_pagination',
    
    # Orders
    'handle_order_request',
    'process_quantity_input',
    'process_name_input',
    'process_phone_input',
    'process_address_input',
    'process_payment_method',
    'confirm_and_create_order',
    'cancel_order',
    'generate_order_number',
    
    # Conversation
    'set_conversation_state',
    'get_conversation_state',
    'update_conversation_data',
    'clear_conversation_state',
    'is_in_conversation',
    'OrderState',
    'validate_phone_number',
    'validate_quantity',
    'validate_name',
    'validate_address',
    
    # Notifications
    'notify_new_order',
    'notify_low_stock',
    'notify_order_cancelled',
    'notify_payment_received',
    'notify_admins_messenger',
]
