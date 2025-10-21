"""
Verification Service Module
Handles order verification for fraud prevention
- ID verification (upload ID + selfie)
- Upfront payment verification (10%)
"""
import logging
from datetime import datetime, timedelta
from services.db_service import get_db_connection
from services.messenger_service import send_message, send_button_template

logger = logging.getLogger(__name__)

# ================================================
# VERIFICATION REQUIREMENTS
# ================================================
VERIFICATION_EXPIRY_HOURS = 1  # 1 hour to complete verification
UPFRONT_PERCENTAGE = 0.10  # 10% upfront payment
COD_VERIFICATION_THRESHOLD = 5000  # Orders above ₱5000 require verification

def check_verification_required(order_total, payment_method, user_id):
    """
    Check if verification is required for this order
    
    Args:
        order_total: Total order amount
        payment_method: Payment method chosen
        user_id: User ID
    
    Returns:
        dict: {required: bool, reason: str, can_skip: bool}
    """
    try:
        # Check if user is trusted buyer
        if is_trusted_buyer(user_id):
            return {
                'required': False,
                'reason': 'trusted_buyer',
                'can_skip': True
            }
        
        # COD orders above threshold require verification
        if payment_method == 'cod' and order_total >= COD_VERIFICATION_THRESHOLD:
            return {
                'required': True,
                'reason': 'cod_high_value',
                'can_skip': False
            }
        
        # All COD orders from new users require verification
        if payment_method == 'cod' and is_new_user(user_id):
            return {
                'required': True,
                'reason': 'new_user_cod',
                'can_skip': False
            }
        
        return {
            'required': False,
            'reason': 'not_required',
            'can_skip': True
        }
        
    except Exception as e:
        logger.error(f"Error checking verification requirement: {e}")
        return {
            'required': False,
            'reason': 'error',
            'can_skip': True
        }

def is_trusted_buyer(user_id):
    """Check if user is a trusted buyer who can skip verification"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT verification_skip_enabled 
            FROM trusted_buyers 
            WHERE user_id = %s AND verification_skip_enabled = TRUE
        """, (user_id,))
        
        result = cursor.fetchone()
        return result is not None
        
    except Exception as e:
        logger.error(f"Error checking trusted buyer: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def is_new_user(user_id):
    """Check if user has less than 3 successful orders"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT total_orders FROM users WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        return result and result['total_orders'] < 3
        
    except Exception as e:
        logger.error(f"Error checking new user: {e}")
        return True
    finally:
        cursor.close()
        conn.close()

# ================================================
# VERIFICATION INITIATION
# ================================================
def initiate_verification(messenger_id, order_id, order_total):
    """
    Send verification options to user
    
    Args:
        messenger_id: User's messenger ID
        order_id: Order ID
        order_total: Total order amount
    """
    upfront_amount = order_total * UPFRONT_PERCENTAGE
    remaining = order_total - upfront_amount
    
    message = (
        f"🛡️ *SECURE ORDER VERIFICATION*\n\n"
        f"Before we proceed, we need to confirm your identity for fraud prevention "
        f"and smoother delivery.\n\n"
        f"You have two options to verify your order:\n\n"
        f"🔘 *Option 1:* Verify using a Valid ID\n"
        f"   (Recommended for COD orders)\n\n"
        f"🔘 *Option 2:* Pay a 10% upfront amount\n"
        f"   (₱{upfront_amount:,.2f}) to confirm instantly\n\n"
        f"Please select your preferred option to continue."
    )
    
    buttons = [
        {
            "type": "postback",
            "title": "📸 ID Verification",
            "payload": f"VERIFY_ID_{order_id}"
        },
        {
            "type": "postback",
            "title": "💳 10% Upfront Payment",
            "payload": f"VERIFY_UPFRONT_{order_id}"
        }
    ]
    
    send_button_template(messenger_id, message, buttons)
    
    # Create verification record
    create_verification_record(order_id, order_total)

def create_verification_record(order_id, order_total):
    """Create verification record in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update order
        expires_at = datetime.now() + timedelta(hours=VERIFICATION_EXPIRY_HOURS)
        upfront_amount = order_total * UPFRONT_PERCENTAGE
        
        cursor.execute("""
            UPDATE orders 
            SET verification_required = TRUE,
                verification_status = 'pending',
                verification_expires_at = %s,
                upfront_paid = 0.00,
                remaining_balance = %s
            WHERE id = %s
        """, (expires_at, order_total, order_id))
        
        conn.commit()
        logger.info(f"✅ Verification record created for order {order_id}")
        
    except Exception as e:
        logger.error(f"Error creating verification record: {e}")
    finally:
        cursor.close()
        conn.close()

# ================================================
# ID VERIFICATION FLOW
# ================================================
def start_id_verification(messenger_id, order_id):
    """Start ID verification process"""
    message = (
        f"📸 *ID VERIFICATION*\n\n"
        f"Great! Please upload a clear photo of your valid ID here.\n\n"
        f"✅ Accepted IDs:\n"
        f"• UMID\n"
        f"• Driver's License\n"
        f"• Passport\n"
        f"• Student ID\n"
        f"• Company ID\n\n"
        f"⚠️ Make sure your *name, photo, and ID number* are clearly visible.\n\n"
        f"📤 Simply send the photo here."
    )
    
    send_message(messenger_id, message)
    
    # Update conversation state
    from services.conversation_service import set_conversation_state
    set_conversation_state(messenger_id, 'AWAITING_ID_UPLOAD', {'order_id': order_id})

def handle_id_upload(messenger_id, order_id, image_url, id_type='Unknown'):
    """Handle ID image upload"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT id FROM users WHERE messenger_id = %s", (messenger_id,))
        user = cursor.fetchone()
        
        if not user:
            send_message(messenger_id, "❌ Error: User not found.")
            return False
        
        # Save ID image (reset status to pending if resubmitting)
        cursor.execute("""
            INSERT INTO order_verifications (
                order_id, user_id, verification_type, 
                verification_status, id_image_url, id_type
            ) VALUES (%s, %s, 'id_verification', 'pending', %s, %s)
            ON DUPLICATE KEY UPDATE 
                id_image_url = %s, 
                id_type = %s,
                verification_status = 'pending',
                selfie_image_url = NULL,
                rejection_reason = NULL,
                submitted_at = NOW()
        """, (order_id, user['id'], image_url, id_type, image_url, id_type))
        
        conn.commit()
        
        # Request selfie
        message = (
            f"✅ *ID received!*\n\n"
            f"Now, please take a *selfie while holding your valid ID* "
            f"so we can confirm that it matches your identity.\n\n"
            f"📸 Make sure both your *face and the ID* are clearly visible.\n\n"
            f"📤 Send your selfie here."
        )
        
        send_message(messenger_id, message)
        
        # Update state to await selfie
        from services.conversation_service import set_conversation_state
        set_conversation_state(messenger_id, 'AWAITING_SELFIE_UPLOAD', {'order_id': order_id})
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling ID upload: {e}")
        send_message(messenger_id, "❌ Error saving ID. Please try again.")
        return False
    finally:
        cursor.close()
        conn.close()

def handle_selfie_upload(messenger_id, order_id, image_url):
    """Handle selfie image upload"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update verification with selfie (resubmission sets to under_review)
        cursor.execute("""
            UPDATE order_verifications 
            SET selfie_image_url = %s,
                verification_status = 'under_review',
                rejection_reason = NULL,
                reviewed_by = NULL,
                reviewed_at = NULL,
                submitted_at = NOW()
            WHERE order_id = %s
        """, (image_url, order_id))
        
        # Update order status (reset if was rejected)
        cursor.execute("""
            UPDATE orders 
            SET verification_status = 'under_review'
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        
        # Send confirmation
        message = (
            f"⏳ *VERIFICATION SUBMITTED*\n\n"
            f"Thank you! Your ID and selfie are now under review.\n\n"
            f"✅ You'll receive a confirmation message once your verification "
            f"is approved (usually within 1-2 hours).\n\n"
            f"📱 We'll notify you here in Messenger.\n\n"
            f"Thank you for your patience! 🙏"
        )
        
        send_message(messenger_id, message)
        
        # Clear conversation state
        from services.conversation_service import clear_conversation_state
        clear_conversation_state(messenger_id)
        
        # Notify admin
        notify_admin_verification_pending(order_id)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling selfie upload: {e}")
        send_message(messenger_id, "❌ Error saving selfie. Please try again.")
        return False
    finally:
        cursor.close()
        conn.close()

# ================================================
# UPFRONT PAYMENT FLOW
# ================================================
def start_upfront_payment(messenger_id, order_id):
    """Start upfront payment process"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get order details
        cursor.execute("""
            SELECT total_amount FROM orders WHERE id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            send_message(messenger_id, "❌ Order not found.")
            return False
        
        total_amount = float(order['total_amount'])
        upfront_amount = total_amount * UPFRONT_PERCENTAGE
        remaining = total_amount - upfront_amount
        
        message = (
            f"💳 *10% UPFRONT PAYMENT*\n\n"
            f"You've chosen to skip ID verification.\n\n"
            f"To confirm your order, please pay 10% of your total order amount upfront.\n\n"
            f"💰 *Order Summary:*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Total Amount: ₱{total_amount:,.2f}\n"
            f"Upfront (10%): *₱{upfront_amount:,.2f}*\n"
            f"Remaining Balance: ₱{remaining:,.2f}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"The remaining balance can be paid upon delivery.\n\n"
            f"Please select your payment method:"
        )
        
        buttons = [
            {"type": "postback", "title": "📱 GCash", "payload": f"PAY_UPFRONT_GCASH_{order_id}"},
            {"type": "postback", "title": "💳 Maya", "payload": f"PAY_UPFRONT_MAYA_{order_id}"},
            {"type": "postback", "title": "🏦 Bank Transfer", "payload": f"PAY_UPFRONT_BANK_{order_id}"}
        ]
        
        send_button_template(messenger_id, message, buttons)
        
        return True
        
    except Exception as e:
        logger.error(f"Error starting upfront payment: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def send_payment_instructions(messenger_id, order_id, payment_method):
    """Send payment instructions for upfront payment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get order details
        cursor.execute("SELECT total_amount FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return False
        
        upfront_amount = float(order['total_amount']) * UPFRONT_PERCENTAGE
        
        payment_details = {
            'gcash': {
                'number': '09171234567',  # Update with actual GCash number
                'name': 'QuickSell Store'
            },
            'maya': {
                'number': '09171234567',  # Update with actual Maya number
                'name': 'QuickSell Store'
            },
            'bank': {
                'bank': 'BDO',
                'account': '1234567890',
                'name': 'QuickSell Store'
            }
        }
        
        if payment_method == 'gcash':
            message = (
                f"📱 *GCASH PAYMENT*\n\n"
                f"Please send *₱{upfront_amount:,.2f}* to:\n\n"
                f"GCash Number: *{payment_details['gcash']['number']}*\n"
                f"Account Name: *{payment_details['gcash']['name']}*\n\n"
                f"Once payment is made, kindly upload a screenshot of your transaction here.\n\n"
                f"⏰ Complete within 1 hour to secure your order."
            )
        elif payment_method == 'maya':
            message = (
                f"💳 *MAYA PAYMENT*\n\n"
                f"Please send *₱{upfront_amount:,.2f}* to:\n\n"
                f"Maya Number: *{payment_details['maya']['number']}*\n"
                f"Account Name: *{payment_details['maya']['name']}*\n\n"
                f"Once payment is made, kindly upload a screenshot of your transaction here.\n\n"
                f"⏰ Complete within 1 hour to secure your order."
            )
        else:  # bank
            message = (
                f"🏦 *BANK TRANSFER*\n\n"
                f"Please transfer *₱{upfront_amount:,.2f}* to:\n\n"
                f"Bank: *{payment_details['bank']['bank']}*\n"
                f"Account #: *{payment_details['bank']['account']}*\n"
                f"Account Name: *{payment_details['bank']['name']}*\n\n"
                f"Once payment is made, kindly upload a screenshot of your deposit slip here.\n\n"
                f"⏰ Complete within 1 hour to secure your order."
            )
        
        send_message(messenger_id, message)
        
        # Update conversation state
        from services.conversation_service import set_conversation_state
        set_conversation_state(messenger_id, 'AWAITING_PAYMENT_PROOF', {
            'order_id': order_id,
            'payment_method': payment_method,
            'amount': upfront_amount
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending payment instructions: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def handle_payment_proof(messenger_id, order_id, image_url, payment_method, amount):
    """Handle payment proof upload"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id
        cursor.execute("SELECT id FROM users WHERE messenger_id = %s", (messenger_id,))
        user = cursor.fetchone()
        
        if not user:
            return False
        
        # Create/update verification record (reset status if resubmitting)
        cursor.execute("""
            INSERT INTO order_verifications (
                order_id, user_id, verification_type,
                verification_status, upfront_amount, 
                payment_proof_url, payment_method
            ) VALUES (%s, %s, 'upfront_payment', 'under_review', %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                upfront_amount = %s,
                payment_proof_url = %s,
                payment_method = %s,
                verification_status = 'under_review',
                rejection_reason = NULL,
                reviewed_by = NULL,
                reviewed_at = NULL,
                submitted_at = NOW()
        """, (order_id, user['id'], amount, image_url, payment_method,
              amount, image_url, payment_method))
        
        # Update order
        cursor.execute("""
            UPDATE orders 
            SET verification_status = 'under_review',
                verification_type = 'upfront_payment'
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        
        # Send confirmation
        remaining = float(cursor.execute(
            "SELECT total_amount - %s FROM orders WHERE id = %s", 
            (amount, order_id)
        ).fetchone()[0])
        
        message = (
            f"⏳ *PAYMENT PROOF RECEIVED*\n\n"
            f"Thank you! Your payment proof is now under review.\n\n"
            f"✅ Once verified (usually within 1-2 hours), your order will be confirmed "
            f"and queued for processing.\n\n"
            f"💰 Remaining balance: *₱{remaining:,.2f}*\n"
            f"(Payable upon delivery)\n\n"
            f"📱 We'll notify you here in Messenger."
        )
        
        send_message(messenger_id, message)
        
        # Clear conversation state
        from services.conversation_service import clear_conversation_state
        clear_conversation_state(messenger_id)
        
        # Notify admin
        notify_admin_payment_verification_pending(order_id, amount)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling payment proof: {e}")
        send_message(messenger_id, "❌ Error saving payment proof. Please try again.")
        return False
    finally:
        cursor.close()
        conn.close()

# ================================================
# ADMIN NOTIFICATIONS
# ================================================
def notify_admin_verification_pending(order_id):
    """Notify admin of pending ID verification"""
    from services.notification_service import notify_admins_messenger
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT o.order_number, u.facebook_name, o.total_amount
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if order:
            message = (
                f"🛡️ *NEW VERIFICATION REQUEST*\n\n"
                f"📋 Order: {order['order_number']}\n"
                f"👤 Customer: {order['facebook_name']}\n"
                f"💰 Amount: ₱{order['total_amount']:,.2f}\n"
                f"📸 Type: ID Verification\n\n"
                f"⚠️ Requires review in admin dashboard"
            )
            
            notify_admins_messenger(message)
        
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")
    finally:
        cursor.close()
        conn.close()

def notify_admin_payment_verification_pending(order_id, amount):
    """Notify admin of pending payment verification"""
    from services.notification_service import notify_admins_messenger
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT o.order_number, u.facebook_name, o.total_amount
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if order:
            message = (
                f"💳 *NEW PAYMENT VERIFICATION*\n\n"
                f"📋 Order: {order['order_number']}\n"
                f"👤 Customer: {order['facebook_name']}\n"
                f"💰 Upfront: ₱{amount:,.2f}\n"
                f"💵 Total: ₱{order['total_amount']:,.2f}\n\n"
                f"⚠️ Requires review in admin dashboard"
            )
            
            notify_admins_messenger(message)
        
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")
    finally:
        cursor.close()
        conn.close()

# ================================================
# VERIFICATION APPROVAL/REJECTION
# ================================================
def approve_verification(order_id, admin_id=None):
    """Approve verification and proceed with order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update verification
        cursor.execute("""
            UPDATE order_verifications
            SET verification_status = 'approved',
                reviewed_by = %s,
                reviewed_at = NOW()
            WHERE order_id = %s
        """, (admin_id, order_id))
        
        # Update order
        cursor.execute("""
            UPDATE orders
            SET verification_status = 'verified',
                order_status = 'confirmed'
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        
        # Get user messenger_id
        cursor.execute("""
            SELECT u.messenger_id, o.order_number, o.total_amount
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        result = cursor.fetchone()
        
        if result:
            message = (
                f"🟢 *VERIFICATION APPROVED!*\n\n"
                f"✅ Your identity has been verified successfully!\n\n"
                f"📋 Order #{result['order_number']}\n"
                f"💰 Total: ₱{result['total_amount']:,.2f}\n\n"
                f"Your order is now confirmed and will be processed shortly.\n\n"
                f"📦 You'll receive tracking updates here in Messenger.\n\n"
                f"Thank you for shopping with QuickSell! 🎉"
            )
            
            send_message(result['messenger_id'], message)
        
        logger.info(f"✅ Verification approved for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error approving verification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def reject_verification(order_id, reason, admin_id=None):
    """Reject verification and cancel order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update verification
        cursor.execute("""
            UPDATE order_verifications
            SET verification_status = 'rejected',
                reviewed_by = %s,
                reviewed_at = NOW(),
                rejection_reason = %s
            WHERE order_id = %s
        """, (admin_id, reason, order_id))
        
        # Update order (keep as pending, allow retry)
        cursor.execute("""
            UPDATE orders
            SET verification_status = 'rejected'
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        
        # Get user messenger_id
        cursor.execute("""
            SELECT u.messenger_id, o.order_number
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        result = cursor.fetchone()
        
        if result:
            message = (
                f"❌ *VERIFICATION REJECTED*\n\n"
                f"📋 Order #{result['order_number']}\n\n"
                f"Reason: {reason}\n\n"
                f"You may submit a new verification below:"
            )
            
            buttons = [
                {
                    "type": "postback",
                    "title": "📸 Submit ID Again",
                    "payload": f"VERIFY_ID_{order_id}"
                },
                {
                    "type": "postback",
                    "title": "💳 Pay 10% Upfront",
                    "payload": f"VERIFY_UPFRONT_{order_id}"
                }
            ]
            
            send_button_template(result['messenger_id'], message, buttons)
        
        logger.info(f"❌ Verification rejected for order {order_id}: {reason}")
        return True
        
    except Exception as e:
        logger.error(f"Error rejecting verification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
