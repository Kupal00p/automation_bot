"""
Order service module
Enterprise-level order processing with multi-step confirmation
"""
import logging
from datetime import datetime
from decimal import Decimal
from services.db_service import get_db_connection, log_chat
from services.messenger_service import send_button_template, send_message
from services.conversation_service import (
    set_conversation_state, get_conversation_state, update_conversation_data,
    clear_conversation_state, OrderState, validate_phone_number,
    validate_quantity, validate_name, validate_address
)
from services.notification_service import notify_new_order, notify_low_stock

logger = logging.getLogger(__name__)

# ================================================
# ORDER INITIATION
# ================================================
def handle_order_request(sender_id, product_id):
    """
    Initiate order flow - Step 1: Start order process
    
    Args:
        sender_id: Facebook user ID
        product_id: Product ID to order
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get product details with full info
        cursor.execute("""
            SELECT p.id, p.name, p.base_price, p.stock_quantity, p.sku,
                   b.name as brand_name, c.name as category_name
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.status = 'active'
        """, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            send_message(sender_id, "Sorry, this product is not available.")
            return
        
        # Check stock
        if product['stock_quantity'] <= 0:
            send_button_template(
                sender_id,
                f"😔 Sorry, {product['name']} is currently out of stock.\n\nWould you like to browse other products?",
                [
                    {"type": "postback", "title": "🛍️ Browse Products", "payload": "VIEW_PRODUCTS"},
                    {"type": "postback", "title": "🔙 Main Menu", "payload": "MAIN_MENU"}
                ]
            )
            return
        
        # Initialize order conversation state
        order_data = {
            'product_id': product_id,
            'product_name': product['name'],
            'product_price': float(product['base_price']),
            'sku': product['sku'],
            'max_stock': product['stock_quantity'],
            'brand_name': product['brand_name'],
            'category_name': product['category_name']
        }
        
        set_conversation_state(sender_id, OrderState.AWAITING_QUANTITY, order_data)
        
        # Ask for quantity
        msg = (
            f"🛒 *ORDER CHECKOUT*\n\n"
            f"📦 {product['name']}\n"
            f"💵 ₱{product['base_price']:,.2f}\n"
            f"📊 Available Stock: {product['stock_quantity']}\n\n"
            f"How many would you like to order?\n"
            f"(Type a number from 1 to {min(product['stock_quantity'], 99)})"
        )
        
        send_button_template(
            sender_id,
            msg,
            [{"type": "postback", "title": "❌ Cancel Order", "payload": "CANCEL_ORDER"}]
        )
        
        logger.info(f"📝 Order initiated for user {sender_id}, product {product_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_order_request: {e}")
        send_message(sender_id, "Sorry, something went wrong. Please try again or type 'menu'.")
    finally:
        cursor.close()
        conn.close()  # Already using putconn

# ================================================
# ORDER FLOW HANDLERS
# ================================================
def process_quantity_input(sender_id, quantity_text):
    """
    Process quantity input - Step 2
    
    Args:
        sender_id: User ID
        quantity_text: Quantity as text
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_QUANTITY:
        return False
    
    # Validate quantity
    is_valid, result = validate_quantity(quantity_text)
    
    if not is_valid:
        send_message(sender_id, f"❌ {result}\n\nPlease enter a valid quantity:")
        return True
    
    quantity = result
    max_stock = state['data']['max_stock']
    
    # Check against available stock
    if quantity > max_stock:
        send_message(sender_id, f"❌ Only {max_stock} units available.\n\nPlease enter a quantity up to {max_stock}:")
        return True
    
    # Update order data
    update_conversation_data(sender_id, 'quantity', quantity)
    
    # Calculate subtotal
    unit_price = Decimal(str(state['data']['product_price']))
    subtotal = unit_price * quantity
    update_conversation_data(sender_id, 'subtotal', float(subtotal))
    
    # Move to next step: Ask for recipient name
    state['state'] = OrderState.AWAITING_NAME
    
    msg = (
        f"✅ Quantity: {quantity}\n"
        f"💰 Subtotal: ₱{subtotal:,.2f}\n\n"
        f"📝 Please enter the *recipient's full name*:"
    )
    
    send_button_template(
        sender_id,
        msg,
        [{"type": "postback", "title": "❌ Cancel Order", "payload": "CANCEL_ORDER"}]
    )
    
    return True

def process_name_input(sender_id, name_text):
    """
    Process recipient name - Step 3
    
    Args:
        sender_id: User ID
        name_text: Name input
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_NAME:
        return False
    
    # Validate name
    is_valid, result = validate_name(name_text)
    
    if not is_valid:
        send_message(sender_id, f"❌ {result}\n\nPlease enter the recipient's full name:")
        return True
    
    # Update order data
    update_conversation_data(sender_id, 'recipient_name', result)
    
    # Move to next step: Ask for phone number
    state['state'] = OrderState.AWAITING_PHONE
    
    send_button_template(
        sender_id,
        f"✅ Recipient: {result}\n\n📱 Please enter your *contact number*:\n(Format: 09XXXXXXXXX or +639XXXXXXXXX)",
        [{"type": "postback", "title": "❌ Cancel Order", "payload": "CANCEL_ORDER"}]
    )
    
    return True

def process_phone_input(sender_id, phone_text):
    """
    Process phone number - Step 4
    
    Args:
        sender_id: User ID
        phone_text: Phone number input
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_PHONE:
        return False
    
    # Validate phone
    is_valid, result = validate_phone_number(phone_text)
    
    if not is_valid:
        send_message(sender_id, f"❌ {result}\n\nPlease enter a valid phone number:")
        return True
    
    # Update order data
    update_conversation_data(sender_id, 'phone', result)
    
    # Move to next step: Ask for delivery address
    state['state'] = OrderState.AWAITING_ADDRESS
    
    send_button_template(
        sender_id,
        f"✅ Phone: {result}\n\n📍 Please enter your *complete delivery address*:\n(Include street, barangay, city, province)",
        [{"type": "postback", "title": "❌ Cancel Order", "payload": "CANCEL_ORDER"}]
    )
    
    return True

def process_address_input(sender_id, address_text):
    """
    Process delivery address - Step 5
    
    Args:
        sender_id: User ID
        address_text: Address input
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_ADDRESS:
        return False
    
    # Validate address
    is_valid, result = validate_address(address_text)
    
    if not is_valid:
        send_message(sender_id, f"❌ {result}\n\nPlease enter your complete delivery address:")
        return True
    
    # Update order data
    update_conversation_data(sender_id, 'address', result)
    
    # Move to next step: Ask for payment method
    state['state'] = OrderState.AWAITING_PAYMENT_METHOD
    
    send_button_template(
        sender_id,
        f"✅ Address: {result[:100]}...\n\n💳 Please select your *payment method*:",
        [
            {"type": "postback", "title": "💵 Cash on Delivery", "payload": "PAY_COD"},
            {"type": "postback", "title": "📱 GCash", "payload": "PAY_GCASH"},
            {"type": "postback", "title": "❌ Cancel", "payload": "CANCEL_ORDER"}
        ]
    )
    
    return True

def process_payment_method(sender_id, payment_method):
    """
    Process payment method selection - Step 6: Show order summary
    
    Args:
        sender_id: User ID
        payment_method: Selected payment method (cod, gcash, etc.)
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_PAYMENT_METHOD:
        return False
    
    # Update order data
    update_conversation_data(sender_id, 'payment_method', payment_method)
    
    # Calculate totals
    data = state['data']
    subtotal = Decimal(str(data['subtotal']))
    shipping_fee = Decimal('50.00')  # Default shipping, can be calculated based on location
    total = subtotal + shipping_fee
    
    update_conversation_data(sender_id, 'shipping_fee', float(shipping_fee))
    update_conversation_data(sender_id, 'total_amount', float(total))
    
    # Move to confirmation step
    state['state'] = OrderState.AWAITING_CONFIRMATION
    
    # Build order summary
    payment_labels = {
        'cod': 'Cash on Delivery (COD)',
        'gcash': 'GCash',
        'bank_transfer': 'Bank Transfer',
        'credit_card': 'Credit Card'
    }
    
    summary = (
        f"📋 *ORDER SUMMARY*\n\n"
        f"📦 Product: {data['product_name']}\n"
        f"🔢 Quantity: {data['quantity']}\n"
        f"💵 Unit Price: ₱{data['product_price']:,.2f}\n"
        f"➖➖➖➖➖➖➖\n"
        f"💰 Subtotal: ₱{subtotal:,.2f}\n"
        f"🚚 Shipping: ₱{shipping_fee:,.2f}\n"
        f"➖➖➖➖➖➖➖\n"
        f"💳 *TOTAL: ₱{total:,.2f}*\n\n"
        f"👤 Recipient: {data['recipient_name']}\n"
        f"📱 Phone: {data['phone']}\n"
        f"📍 Address: {data['address'][:80]}...\n"
        f"💳 Payment: {payment_labels.get(payment_method, payment_method)}\n\n"
        f"✅ Confirm this order?"
    )
    
    send_button_template(
        sender_id,
        summary[:640],  # FB limit
        [
            {"type": "postback", "title": "✅ CONFIRM ORDER", "payload": "CONFIRM_ORDER"},
            {"type": "postback", "title": "❌ Cancel", "payload": "CANCEL_ORDER"}
        ]
    )
    
    return True

# ================================================
# ORDER CONFIRMATION & DATABASE
# ================================================
def confirm_and_create_order(sender_id):
    """
    Final confirmation and order creation - Step 7: Save to database
    
    Args:
        sender_id: User ID
    
    Returns:
        bool: True if successful
    """
    state = get_conversation_state(sender_id)
    if not state or state['state'] != OrderState.AWAITING_CONFIRMATION:
        send_message(sender_id, "❌ No active order to confirm. Please start a new order.")
        return False
    
    data = state['data']
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Start transaction
        conn.start_transaction()
        
        # 1. Get user ID from database
        cursor.execute("SELECT id FROM users WHERE messenger_id = %s", (sender_id,))
        user = cursor.fetchone()
        
        if not user:
            raise Exception("User not found")
        
        user_id = user['id']
        
        # 2. Check product stock again (prevent race conditions)
        cursor.execute("""
            SELECT stock_quantity, base_price 
            FROM products 
            WHERE id = %s FOR UPDATE
        """, (data['product_id'],))
        product = cursor.fetchone()
        
        if not product or product['stock_quantity'] < data['quantity']:
            conn.rollback()
            send_message(sender_id, "❌ Sorry, insufficient stock. Order cannot be processed.")
            clear_conversation_state(sender_id)
            return False
        
        # 3. Generate order number
        order_number = generate_order_number()
        
        # 4. Insert order
        cursor.execute("""
            INSERT INTO orders (
                order_number, user_id, subtotal, shipping_fee, 
                total_amount, payment_method, payment_status, 
                order_status, notes, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            order_number,
            user_id,
            data['subtotal'],
            data['shipping_fee'],
            data['total_amount'],
            data['payment_method'],
            'pending',
            'pending',
            f"Recipient: {data['recipient_name']}, Phone: {data['phone']}, Address: {data['address']}"
        ))
        
        order_id = cursor.lastrowid
        
        # 5. Insert order item
        cursor.execute("""
            INSERT INTO order_items (
                order_id, product_id, product_name, sku, 
                quantity, unit_price, total_price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id,
            data['product_id'],
            data['product_name'],
            data['sku'],
            data['quantity'],
            data['product_price'],
            data['subtotal']
        ))
        
        # 6. Update product stock
        new_stock = product['stock_quantity'] - data['quantity']
        cursor.execute("""
            UPDATE products 
            SET stock_quantity = %s, sales_count = sales_count + %s
            WHERE id = %s
        """, (new_stock, data['quantity'], data['product_id']))
        
        # 7. Log inventory change
        cursor.execute("""
            INSERT INTO inventory_logs (
                product_id, transaction_type, quantity_change,
                previous_stock, new_stock, reference_type, reference_id
            ) VALUES (%s, 'stock_out', %s, %s, %s, 'order', %s)
        """, (
            data['product_id'],
            -data['quantity'],
            product['stock_quantity'],
            new_stock,
            order_id
        ))
        
        # 8. Update user statistics
        cursor.execute("""
            UPDATE users 
            SET total_orders = total_orders + 1,
                total_spent = total_spent + %s
            WHERE id = %s
        """, (data['total_amount'], user_id))
        
        # Commit transaction
        conn.commit()
        
        # 9. Check if verification is required (COD orders)
        from services.verification_service import check_verification_required, initiate_verification
        
        verification_check = check_verification_required(
            data['total_amount'], 
            data['payment_method'],
            user_id
        )
        
        if verification_check['required']:
            # Commit the order but keep it as 'pending' status
            conn.commit()
            
            # Initiate verification process
            initiate_verification(sender_id, order_id, data['total_amount'])
            
            logger.info(f"🛡️ Order {order_number} requires verification - initiated")
            return True
        
        # 10. Send success message with order number (no verification required)
        confirmation_msg = (
            f"✅ *ORDER CONFIRMED!*\n\n"
            f"📋 Order Number: *{order_number}*\n"
            f"💰 Total: *₱{data['total_amount']:,.2f}*\n\n"
            f"Your order has been received and is being processed!\n\n"
            f"📦 Delivery to:\n"
            f"{data['recipient_name']}\n"
            f"{data['address']}\n\n"
            f"📱 We'll contact you at {data['phone']} for confirmation.\n\n"
            f"Thank you for shopping with QuickSell! 🎉"
        )
        
        send_button_template(
            sender_id,
            confirmation_msg,
            [
                {"type": "postback", "title": "🛍️ Shop More", "payload": "VIEW_PRODUCTS"},
                {"type": "postback", "title": "🏠 Main Menu", "payload": "MAIN_MENU"}
            ]
        )
        
        # 11. Notify admins
        notify_new_order({
            'order_number': order_number,
            'customer_name': data['recipient_name'],
            'phone': data['phone'],
            'product_name': data['product_name'],
            'quantity': data['quantity'],
            'total_amount': data['total_amount'],
            'payment_method': data['payment_method'],
            'address': data['address'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 12. Check for low stock and notify
        if new_stock <= 5:
            notify_low_stock(data['product_name'], new_stock, 5)
        
        # 13. Log chat
        log_chat(sender_id, f"ORDER_CONFIRMED_{order_number}", "Order successfully created", 'order_complete')
        
        # Clear conversation state
        clear_conversation_state(sender_id)
        
        logger.info(f"✅ Order {order_number} created successfully for user {sender_id}")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Error creating order: {e}")
        send_message(sender_id, "❌ Failed to create order. Please try again or contact support.")
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()  # Already using putconn

def cancel_order(sender_id):
    """
    Cancel ongoing order
    
    Args:
        sender_id: User ID
    """
    state = get_conversation_state(sender_id)
    
    if state:
        clear_conversation_state(sender_id)
        send_button_template(
            sender_id,
            "❌ Order cancelled.\n\nWhat would you like to do next?",
            [
                {"type": "postback", "title": "🛍️ Browse Products", "payload": "VIEW_PRODUCTS"},
                {"type": "postback", "title": "🏠 Main Menu", "payload": "MAIN_MENU"}
            ]
        )
        log_chat(sender_id, "CANCEL_ORDER", "Order cancelled by user", 'order_cancelled')
    else:
        send_message(sender_id, "No active order to cancel.")

# ================================================
# HELPER FUNCTIONS
# ================================================
def generate_order_number():
    """
    Generate unique order number
    
    Returns:
        str: Order number (format: ORD-YYYYMMDD-XXXXX)
    """
    from datetime import datetime
    import random
    
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = str(random.randint(10000, 99999))
    
    return f"ORD-{date_part}-{random_part}"
