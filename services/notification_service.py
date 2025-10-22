"""
Notification service module
Handles admin notifications for new orders and important events
"""
import logging
import os
import requests
from services.messenger_service import send_message
from services.db_service import get_db_connection

logger = logging.getLogger(__name__)

# Admin notification channels
ADMIN_MESSENGER_IDS = os.getenv("ADMIN_MESSENGER_IDS", "").split(",")  # Comma-separated messenger IDs
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@quicksell.com")
WEBHOOK_URL = os.getenv("ADMIN_WEBHOOK_URL", "")  # For Slack/Discord/Custom webhooks

# ================================================
# MESSENGER NOTIFICATIONS
# ================================================
def notify_admins_messenger(message):
    """
    Send notification to all admin Messenger accounts
    
    Args:
        message: Notification message text
    """
    if not ADMIN_MESSENGER_IDS or ADMIN_MESSENGER_IDS == ['']:
        logger.warning("⚠️ No admin Messenger IDs configured")
        return
    
    for admin_id in ADMIN_MESSENGER_IDS:
        if admin_id.strip():
            try:
                send_message(admin_id.strip(), message)
                logger.info(f"✅ Sent admin notification to {admin_id}")
            except Exception as e:
                logger.error(f"❌ Failed to notify admin {admin_id}: {e}")

def notify_new_order_messenger(order_data):
    """
    Send new order notification to admins via Messenger
    
    Args:
        order_data: Dictionary with order details
    """
    message = (
        f"🔔 *NEW ORDER RECEIVED*\n\n"
        f"📋 Order #: {order_data['order_number']}\n"
        f"👤 Customer: {order_data['customer_name']}\n"
        f"📱 Phone: {order_data['phone']}\n"
        f"📦 Product: {order_data['product_name']}\n"
        f"🔢 Quantity: {order_data['quantity']}\n"
        f"💰 Total: ₱{order_data['total_amount']:,.2f}\n"
        f"💳 Payment: {order_data['payment_method']}\n"
        f"📍 Address: {order_data['address'][:100]}...\n\n"
        f"⏰ {order_data['created_at']}"
    )
    
    notify_admins_messenger(message)

# ================================================
# WEBHOOK NOTIFICATIONS (Slack, Discord, etc.)
# ================================================
def notify_webhook(payload):
    """
    Send notification to webhook endpoint
    
    Args:
        payload: Dictionary to send as JSON
    """
    if not WEBHOOK_URL:
        return
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info("✅ Webhook notification sent")
        else:
            logger.error(f"❌ Webhook failed: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")

def notify_new_order_webhook(order_data):
    """
    Send new order notification to webhook
    
    Args:
        order_data: Dictionary with order details
    """
    payload = {
        "event": "new_order",
        "order_number": order_data['order_number'],
        "customer_name": order_data['customer_name'],
        "phone": order_data['phone'],
        "product_name": order_data['product_name'],
        "quantity": order_data['quantity'],
        "total_amount": float(order_data['total_amount']),
        "payment_method": order_data['payment_method'],
        "address": order_data['address'],
        "created_at": order_data['created_at']
    }
    
    notify_webhook(payload)

# ================================================
# EMAIL NOTIFICATIONS (Future implementation)
# ================================================
def send_email_notification(subject, body, to_email=None):
    """
    Send email notification (placeholder for future implementation)
    
    Args:
        subject: Email subject
        body: Email body
        to_email: Recipient email (defaults to ADMIN_EMAIL)
    """
    # TODO: Implement email sending using SMTP or email service (SendGrid, AWS SES, etc.)
    logger.info(f"📧 Email notification: {subject} (Not implemented yet)")
    pass

# ================================================
# UNIFIED NOTIFICATION FUNCTION
# ================================================
def notify_new_order(order_data):
    """
    Send new order notification through all configured channels
    
    Args:
        order_data: Dictionary with complete order details
            - order_number
            - customer_name
            - phone
            - product_name
            - quantity
            - total_amount
            - payment_method
            - address
            - created_at
    """
    logger.info(f"📢 Notifying admins of new order: {order_data['order_number']}")
    
    # Messenger notifications
    notify_new_order_messenger(order_data)
    
    # Webhook notifications
    notify_new_order_webhook(order_data)
    
    # Email notification (future)
    # send_email_notification(
    #     f"New Order #{order_data['order_number']}",
    #     f"Order from {order_data['customer_name']} - ₱{order_data['total_amount']:,.2f}"
    # )

# ================================================
# OTHER NOTIFICATIONS
# ================================================
def notify_low_stock(product_name, current_stock, threshold):
    """
    Notify admins of low stock
    
    Args:
        product_name: Product name
        current_stock: Current stock level
        threshold: Low stock threshold
    """
    message = (
        f"⚠️ *LOW STOCK ALERT*\n\n"
        f"📦 Product: {product_name}\n"
        f"📊 Current Stock: {current_stock}\n"
        f"🚨 Threshold: {threshold}\n\n"
        f"Please restock soon!"
    )
    
    notify_admins_messenger(message)

def notify_order_cancelled(order_number, customer_name, reason):
    """
    Notify admins of order cancellation
    
    Args:
        order_number: Order number
        customer_name: Customer name
        reason: Cancellation reason
    """
    message = (
        f"❌ *ORDER CANCELLED*\n\n"
        f"📋 Order #: {order_number}\n"
        f"👤 Customer: {customer_name}\n"
        f"💬 Reason: {reason}"
    )
    
    notify_admins_messenger(message)

def notify_payment_received(order_number, amount, payment_method):
    """
    Notify admins of payment received
    
    Args:
        order_number: Order number
        amount: Payment amount
        payment_method: Payment method used
    """
    message = (
        f"💰 *PAYMENT RECEIVED*\n\n"
        f"📋 Order #: {order_number}\n"
        f"💵 Amount: ₱{amount:,.2f}\n"
        f"💳 Method: {payment_method}"
    )
    
    notify_admins_messenger(message)

# ================================================
# ADMIN DASHBOARD DATA
# ================================================
def get_pending_orders_count():
    """
    Get count of pending orders for dashboard
    
    Returns:
        int: Number of pending orders
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'pending'")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"Error getting pending orders count: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()  # Already using putconn

def get_todays_orders():
    """
    Get today's orders for dashboard
    
    Returns:
        dict: Today's order statistics
    """
    try:
        conn = get_db_connection()
        cursor = cursor.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM orders
            WHERE DATE(created_at) = CURDATE()
        """)
        stats = cursor.fetchone()
        return stats
    except Exception as e:
        logger.error(f"Error getting today's orders: {e}")
        return {'total_orders': 0, 'total_sales': 0, 'avg_order_value': 0}
    finally:
        cursor.close()
        conn.close()  # Already using putconn
