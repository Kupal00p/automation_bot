"""
Admin service module
Handles admin dashboard operations and order management
"""
import logging
from datetime import datetime, timedelta
from services.db_service import get_db_connection
from services.messenger_service import send_message, send_button_template
from services.notification_service import notify_payment_received

logger = logging.getLogger(__name__)

# ================================================
# ORDER MANAGEMENT
# ================================================
def get_all_orders(status=None, limit=50, offset=0):
    """
    Get orders for admin dashboard
    
    Args:
        status: Filter by order_status (None = all)
        limit: Number of orders to return
        offset: Pagination offset
    
    Returns:
        list: Order records with customer info
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if status:
            query = """
                SELECT 
                    o.id, o.order_number, o.subtotal, o.shipping_fee, 
                    o.total_amount, o.payment_method, o.payment_status,
                    o.order_status, o.notes, o.created_at,
                    u.messenger_id, u.facebook_name as customer_name, 
                    u.email, u.phone as customer_phone
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.order_status = %s
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (status, limit, offset))
        else:
            query = """
                SELECT 
                    o.id, o.order_number, o.subtotal, o.shipping_fee, 
                    o.total_amount, o.payment_method, o.payment_status,
                    o.order_status, o.notes, o.created_at,
                    u.messenger_id, u.facebook_name as customer_name, 
                    u.email, u.phone as customer_phone
                FROM orders o
                JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (limit, offset))
        
        orders = cursor.fetchall()
        
        # Get order items for each order
        for order in orders:
            cursor.execute("""
                SELECT product_name, variant_details, sku, 
                       quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = %s
            """, (order['id'],))
            order['items'] = cursor.fetchall()
            
            # Parse notes to extract delivery info
            order['delivery_info'] = parse_order_notes(order['notes'])
        
        return orders
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return []
    finally:
        cursor.close()
        conn.close()  # Already using putconn

def get_order_by_id(order_id):
    """
    Get single order details including verification images
    
    Args:
        order_id: Order ID
    
    Returns:
        dict: Order details or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get order with user details
        cursor.execute("""
            SELECT 
                o.*, 
                u.messenger_id, 
                u.facebook_name, 
                u.email, 
                u.phone,
                u.customer_tier,
                COALESCE(u.total_orders, 0) as user_total_orders
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if order:
            # Get order items
            cursor.execute("""
                SELECT * FROM order_items WHERE order_id = %s
            """, (order_id,))
            order['items'] = cursor.fetchall()
            
            # Parse delivery info
            order['delivery_info'] = parse_order_notes(order['notes'])
            
            # Get verification details if exists
            cursor.execute("""
                SELECT 
                    verification_type, verification_status, 
                    id_image_url, selfie_image_url, payment_proof_url,
                    id_type, upfront_amount, payment_method,
                    rejection_reason, submitted_at, reviewed_at
                FROM order_verifications
                WHERE order_id = %s
            """, (order_id,))
            verification = cursor.fetchone()
            order['verification'] = verification if verification else None
        
        return order
        
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()  # Already using putconn

def get_order_by_number(order_number):
    """
    Get order by order number
    
    Args:
        order_number: Order number string
    
    Returns:
        dict: Order details or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                o.*, u.messenger_id, u.facebook_name, u.email, u.phone
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.order_number = %s
        """, (order_number,))
        
        order = cursor.fetchone()
        
        if order:
            cursor.execute("""
                SELECT * FROM order_items WHERE order_id = %s
            """, (order['id'],))
            order['items'] = cursor.fetchall()
            order['delivery_info'] = parse_order_notes(order['notes'])
        
        return order
        
    except Exception as e:
        logger.error(f"Error getting order {order_number}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()  # Already using putconn

# ================================================
# ORDER STATUS UPDATE
# ================================================
def update_order_status(order_id, new_status, notify_customer=True):
    """
    Update order status and notify customer
    
    Args:
        order_id: Order ID
        new_status: New order status
        notify_customer: Whether to notify customer
    
    Returns:
        bool: Success status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get order details first
        order = get_order_by_id(order_id)
        if not order:
            return False
        
        # Update status
        update_query = "UPDATE orders SET order_status = %s"
        params = [new_status]
        
        # Set timestamp based on status
        if new_status == 'confirmed':
            update_query += ", confirmed_at = CURRENT_TIMESTAMP"
        elif new_status == 'shipped':
            update_query += ", shipped_at = CURRENT_TIMESTAMP"
        elif new_status == 'delivered':
            update_query += ", delivered_at = CURRENT_TIMESTAMP"
        elif new_status == 'cancelled':
            update_query += ", cancelled_at = CURRENT_TIMESTAMP"
        
        update_query += " WHERE id = %s"
        params.append(order_id)
        
        cursor.execute(update_query, params)
        conn.commit()
        
        logger.info(f"✅ Order {order['order_number']} status updated to {new_status}")
        
        # Notify customer
        if notify_customer:
            notify_customer_status_change(order, new_status)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return False
    finally:
        cursor.close()
        conn.close()  # Already using putconn

def confirm_order_by_admin(order_id, admin_notes=None):
    """
    Admin confirms order - main function
    
    Args:
        order_id: Order ID
        admin_notes: Optional admin notes
    
    Returns:
        bool: Success status
    """
    conn = None
    cursor = None
    try:
        logger.info(f"🔄 Starting order confirmation for order_id: {order_id}")
        
        # Get order first (uses its own connection)
        order = get_order_by_id(order_id)
        if not order:
            logger.error(f"❌ Order not found: {order_id}")
            return False
        
        logger.info(f"📋 Found order: {order['order_number']}, current status: {order['order_status']}")
        
        # Create new connection for update
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update to confirmed
        update_query = """
            UPDATE orders 
            SET order_status = 'confirmed', 
                confirmed_at = CURRENT_TIMESTAMP
        """
        
        if admin_notes:
            update_query += ", notes = CONCAT(COALESCE(notes, ''), '\nAdmin Notes: ', %s)"
            cursor.execute(update_query + " WHERE id = %s", (admin_notes, order_id))
        else:
            cursor.execute(update_query + " WHERE id = %s", (order_id,))
        
        affected_rows = cursor.rowcount
        logger.info(f"📝 SQL executed, affected rows: {affected_rows}")
        
        conn.commit()
        
        logger.info(f"✅ Admin confirmed order {order['order_number']}")
        
        # Notify customer
        try:
            notify_customer_order_confirmed(order)
            logger.info(f"📧 Customer notification sent for order {order['order_number']}")
        except Exception as notify_error:
            logger.error(f"⚠️ Failed to notify customer, but order was confirmed: {notify_error}")
            # Don't fail the confirmation if notification fails
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error confirming order {order_id}: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()  # Already using putconn

def cancel_order_by_admin(order_id, reason):
    """
    Admin cancels order and restores stock
    
    Args:
        order_id: Order ID
        reason: Cancellation reason
    
    Returns:
        bool: Success status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        conn.start_transaction()
        
        # Get order details
        order = get_order_by_id(order_id)
        if not order:
            return False
        
        # Update order status
        cursor.execute("""
            UPDATE orders 
            SET order_status = 'cancelled', 
                cancelled_at = CURRENT_TIMESTAMP,
                notes = CONCAT(notes, '\nCancelled by Admin: ', %s)
            WHERE id = %s
        """, (reason, order_id))
        
        # Restore stock for each item
        for item in order['items']:
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + %s,
                    sales_count = sales_count - %s
                WHERE id = %s
            """, (item['quantity'], item['quantity'], item['product_id']))
            
            # Log inventory restoration
            cursor.execute("""
                INSERT INTO inventory_logs (
                    product_id, transaction_type, quantity_change,
                    previous_stock, new_stock, reference_type, reference_id, notes
                )
                SELECT 
                    %s, 'return', %s, 
                    stock_quantity - %s, stock_quantity,
                    'order_cancellation', %s, %s
                FROM products WHERE id = %s
            """, (item['product_id'], item['quantity'], item['quantity'], 
                  order_id, reason, item['product_id']))
        
        conn.commit()
        
        logger.info(f"❌ Admin cancelled order {order['order_number']}")
        
        # Notify customer
        notify_customer_order_cancelled(order, reason)
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error cancelling order: {e}")
        return False
    finally:
        cursor.close()
        conn.close()  # Already using putconn

# ================================================
# CUSTOMER NOTIFICATIONS
# ================================================
def notify_customer_order_confirmed(order):
    """
    Notify customer that admin confirmed their order
    
    Args:
        order: Order dictionary
    """
    delivery_info = order['delivery_info']
    
    message = (
        f"✅ *ORDER CONFIRMED BY ADMIN*\n\n"
        f"📋 Order #{order['order_number']}\n"
        f"💰 Total: ₱{order['total_amount']:,.2f}\n\n"
        f"Your order has been confirmed and is now being processed!\n\n"
        f"📦 Delivery to:\n"
        f"{delivery_info.get('recipient_name', 'N/A')}\n"
        f"{delivery_info.get('phone', 'N/A')}\n"
        f"{delivery_info.get('address', 'N/A')}\n\n"
        f"We'll notify you when your order ships.\n\n"
        f"Thank you for shopping with QuickSell! 🎉"
    )
    
    send_message(order['messenger_id'], message)
    logger.info(f"📧 Notified customer {order['messenger_id']} - Order confirmed")

def notify_customer_order_cancelled(order, reason):
    """
    Notify customer that order was cancelled
    
    Args:
        order: Order dictionary
        reason: Cancellation reason
    """
    message = (
        f"❌ *ORDER CANCELLED*\n\n"
        f"📋 Order #{order['order_number']}\n"
        f"💰 Amount: ₱{order['total_amount']:,.2f}\n\n"
        f"Reason: {reason}\n\n"
        f"If you have any questions, please contact our support team.\n\n"
        f"We apologize for any inconvenience."
    )
    
    send_button_template(
        order['messenger_id'],
        message,
        [
            {"type": "postback", "title": "🛍️ Browse Products", "payload": "VIEW_PRODUCTS"},
            {"type": "postback", "title": "🏠 Main Menu", "payload": "MAIN_MENU"}
        ]
    )
    logger.info(f"📧 Notified customer {order['messenger_id']} - Order cancelled")

def notify_customer_status_change(order, new_status):
    """
    Notify customer of status change
    
    Args:
        order: Order dictionary
        new_status: New status
    """
    status_messages = {
        'confirmed': '✅ Your order has been confirmed!',
        'processing': '⚙️ Your order is being processed.',
        'shipped': '🚚 Your order has been shipped!',
        'delivered': '📦 Your order has been delivered!',
        'cancelled': '❌ Your order has been cancelled.'
    }
    
    message = (
        f"📢 *ORDER UPDATE*\n\n"
        f"📋 Order #{order['order_number']}\n"
        f"Status: {status_messages.get(new_status, new_status)}\n\n"
        f"💰 Total: ₱{order['total_amount']:,.2f}"
    )
    
    send_message(order['messenger_id'], message)

# ================================================
# DASHBOARD STATISTICS
# ================================================
def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    
    Returns:
        dict: Dashboard stats with analytics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        stats = {}
        
        # Total orders and revenue (all time)
        cursor.execute("""
            SELECT COUNT(*) as total_orders, 
                   COALESCE(SUM(total_amount), 0) as total_revenue
            FROM orders WHERE order_status != 'cancelled'
        """)
        totals = cursor.fetchone()
        stats['total_orders'] = totals['total_orders']
        stats['total_revenue'] = float(totals['total_revenue'])
        
        # Pending orders
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE order_status = 'pending'")
        stats['pending_orders'] = cursor.fetchone()['count']
        
        # Active users (last 30 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM orders 
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 30 DAY)
        """)
        stats['active_users'] = cursor.fetchone()['count']
        
        # Order status distribution
        cursor.execute("""
            SELECT order_status, COUNT(*) as count
            FROM orders
            GROUP BY order_status
        """)
        status_counts = cursor.fetchall()
        stats['order_status_counts'] = [row['count'] for row in status_counts]
        
        # Weekly sales (last 7 days)
        cursor.execute("""
            SELECT 
                DAYNAME(created_at) as day_name,
                COALESCE(SUM(total_amount), 0) as total
            FROM orders
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)
                AND order_status != 'cancelled'
            GROUP BY DATE(created_at), DAYNAME(created_at)
            ORDER BY DATE(created_at)
        """)
        weekly = cursor.fetchall()
        stats['weekly_sales'] = [float(row['total']) for row in weekly]
        
        # New customers this month (using created_at)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
            WHERE created_at IS NOT NULL 
                AND DATE(created_at) >= DATE_FORMAT(CURRENT_TIMESTAMP, '%Y-%m-01')
        """)
        stats['new_customers'] = cursor.fetchone()['count']
        
        # Repeat customers (>1 order)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
            WHERE total_orders > 1
        """)
        stats['repeat_customers'] = cursor.fetchone()['count']
        
        # Average order value
        cursor.execute("""
            SELECT AVG(total_amount) as avg_val
            FROM orders
            WHERE order_status != 'cancelled'
        """)
        avg_result = cursor.fetchone()
        stats['avg_order_value'] = float(avg_result['avg_val']) if avg_result['avg_val'] else 0
        
        # Top products (by sales count)
        cursor.execute("""
            SELECT p.name, SUM(oi.quantity) as total_sold
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.order_status != 'cancelled'
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT 5
        """)
        top_products = cursor.fetchall()
        stats['top_products'] = top_products
        
        # Low stock alerts
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM products 
            WHERE stock_quantity <= low_stock_threshold AND status = 'active'
        """)
        stats['low_stock_products'] = cursor.fetchone()['count']
        
        # Monthly revenue (last 6 months)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%b') as month_name,
                COALESCE(SUM(total_amount), 0) as total
            FROM orders
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 6 MONTH)
                AND order_status != 'cancelled'
            GROUP BY YEAR(created_at), MONTH(created_at)
            ORDER BY YEAR(created_at), MONTH(created_at)
        """)
        monthly = cursor.fetchall()
        stats['monthly_revenue'] = [float(row['total']) for row in monthly]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            'total_orders': 0,
            'total_revenue': 0,
            'pending_orders': 0,
            'active_users': 0,
            'new_customers': 0,
            'repeat_customers': 0,
            'avg_order_value': 0
        }
    finally:
        cursor.close()
        conn.close()  # Already using putconn

# ================================================
# HELPER FUNCTIONS
# ================================================
def parse_order_notes(notes):
    """
    Parse order notes to extract delivery information
    
    Args:
        notes: Order notes string
    
    Returns:
        dict: Parsed delivery info
    """
    import re
    
    delivery_info = {
        'recipient_name': '',
        'phone': '',
        'address': ''
    }
    
    if not notes:
        return delivery_info
    
    # Extract recipient name
    match = re.search(r'Recipient:\s*(.+?)(?:,|Phone:|$)', notes)
    if match:
        delivery_info['recipient_name'] = match.group(1).strip()
    
    # Extract phone
    match = re.search(r'Phone:\s*(.+?)(?:,|Address:|$)', notes)
    if match:
        delivery_info['phone'] = match.group(1).strip()
    
    # Extract address
    match = re.search(r'Address:\s*(.+?)(?:\n|$)', notes)
    if match:
        delivery_info['address'] = match.group(1).strip()
    
    return delivery_info

def get_recent_activity(limit=10):
    """
    Get recent order activity for dashboard
    
    Args:
        limit: Number of activities to return
    
    Returns:
        list: Recent activities
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT o.order_number, o.order_status, o.total_amount,
                   o.created_at, u.facebook_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT %s
        """, (limit,))
        
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []
    finally:
        cursor.close()
        conn.close()  # Already using putconn
