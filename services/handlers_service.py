"""
Handlers service module
Handles user messages and postback actions
"""
import logging
from config import vectorizer, model
from services.db_service import get_keyword_reply, log_chat
from services.messenger_service import send_message, send_button_template
from services.product_service import (
    show_categories, show_products_page, show_product_details, 
    show_promos, show_shipping_info, user_pagination
)
from services.order_service import (
    handle_order_request, process_quantity_input, process_name_input,
    process_phone_input, process_address_input, process_payment_method,
    confirm_and_create_order, cancel_order
)
from services.conversation_service import is_in_conversation, get_conversation_state, OrderState
from services.verification_service import (
    start_id_verification, handle_id_upload, handle_selfie_upload,
    start_upfront_payment, send_payment_instructions, handle_payment_proof
)

logger = logging.getLogger(__name__)

# ================================================
# USER MESSAGE HANDLER
# ================================================
def handle_user_message(sender_id, text):
    """
    Handle user text messages
    
    Args:
        sender_id: Facebook user ID
        text: User's message text
    """
    text_lower = text.lower()
    greetings = ["hello", "hi", "good morning", "good afternoon", "hey", "kamusta", "kumusta"]
    
    try:
        # ============================================
        # PRIORITY 1: Check if user is in order flow
        # ============================================
        if is_in_conversation(sender_id):
            state = get_conversation_state(sender_id)
            
            # Order flow states
            if state['state'] == OrderState.AWAITING_QUANTITY:
                if process_quantity_input(sender_id, text):
                    return
            
            elif state['state'] == OrderState.AWAITING_NAME:
                if process_name_input(sender_id, text):
                    return
            
            elif state['state'] == OrderState.AWAITING_PHONE:
                if process_phone_input(sender_id, text):
                    return
            
            elif state['state'] == OrderState.AWAITING_ADDRESS:
                if process_address_input(sender_id, text):
                    return
            
            # Verification states - handled in handle_attachment
            elif state['state'] in ['AWAITING_ID_UPLOAD', 'AWAITING_SELFIE_UPLOAD', 'AWAITING_PAYMENT_PROOF']:
                send_message(sender_id, "📸 Please upload an image/photo, not text.")
                return
        
        # ============================================
        # PRIORITY 2: Check chatbot_replies table
        # ============================================
        reply = get_keyword_reply(text_lower)
        if reply:
            send_message(sender_id, reply)
            log_chat(sender_id, text, reply, 'keyword_match')
            return
        
        # ============================================
        # PRIORITY 3: Check for greetings
        # ============================================
        if any(greet in text_lower for greet in greetings):
            response = "👋 Hello! Welcome back to QuickSell!\n\nType 'menu' to explore our products."
            send_message(sender_id, response)
            log_chat(sender_id, text, response, 'greeting')
            return
        
        # ============================================
        # PRIORITY 4: Check for menu command
        # ============================================
        if text_lower == "menu":
            send_main_menu(sender_id)
            log_chat(sender_id, text, "Main menu displayed", 'menu')
            return
        
        # ============================================
        # PRIORITY 5: Use NLP model if available
        # ============================================
        if vectorizer and model:
            X = vectorizer.transform([text])
            intent = model.predict(X)[0]
            logger.info(f"🤖 Detected intent: {intent}")
            
            responses = {
                "price": "Sure! Type 'menu' to browse products and see prices.",
                "stock": "Type 'menu' to check our available stocks!",
                "shipping": "🚚 Check our shipping info:\n\nMetro Manila: ₱50\nProvincial: ₱100\nFree shipping ≥ ₱5000!\n\nType 'menu' to continue.",
                "greetings": "Hello! Type 'menu' anytime to browse our products."
            }
            response = responses.get(intent, "I'm not sure I understood that. Type 'menu' to see our products!")
            send_message(sender_id, response)
            log_chat(sender_id, text, response, intent)
        else:
            response = "Type 'menu' to see what we offer! 🛍️"
            send_message(sender_id, response)
            log_chat(sender_id, text, response, 'fallback')
    
    except Exception as e:
        logger.error(f"Error in handle_user_message: {e}")
        send_message(sender_id, "Sorry, something went wrong. Please try again or type 'menu'.")


# ================================================
# POSTBACK HANDLER
# ================================================
def handle_postback(sender_id, payload):
    """
    Handle button clicks and postbacks
    
    Args:
        sender_id: Facebook user ID
        payload: Postback payload string
    """
    logger.info(f"🔘 Postback: {payload}")
    
    try:
        # ============================================
        # MAIN MENU
        # ============================================
        if payload == "MAIN_MENU":
            send_main_menu(sender_id)
        
        # ============================================
        # PRODUCTS & CATALOG
        # ============================================
        elif payload == "VIEW_PRODUCTS":
            show_categories(sender_id)
        
        elif payload == "SHIPPING_INFO":
            show_shipping_info(sender_id)
        
        elif payload == "VIEW_PROMOS":
            show_promos(sender_id)
        
        elif payload.startswith("CATEGORY_"):
            category_slug = payload.split("_", 1)[1]
            user_pagination[sender_id] = {'category': category_slug, 'page': 0}
            show_products_page(sender_id, category_slug, 0)
        
        # ============================================
        # PAGINATION
        # ============================================
        elif payload == "SHOW_MORE":
            if sender_id in user_pagination:
                user_data = user_pagination[sender_id]
                user_data['page'] += 1
                show_products_page(sender_id, user_data['category'], user_data['page'])
        
        elif payload == "SHOW_PREVIOUS":
            if sender_id in user_pagination:
                user_data = user_pagination[sender_id]
                if user_data['page'] > 0:
                    user_data['page'] -= 1
                    show_products_page(sender_id, user_data['category'], user_data['page'])
        
        # ============================================
        # PRODUCT DETAILS
        # ============================================
        elif payload.startswith("PRODUCT_"):
            product_id = payload.split("_")[1]
            show_product_details(sender_id, product_id)
        
        # ============================================
        # ORDER FLOW
        # ============================================
        elif payload.startswith("ORDER_"):
            product_id = payload.split("_")[1]
            handle_order_request(sender_id, product_id)
        
        # Payment method selection
        elif payload == "PAY_COD":
            process_payment_method(sender_id, 'cod')
        
        elif payload == "PAY_GCASH":
            process_payment_method(sender_id, 'gcash')
        
        elif payload == "PAY_BANK":
            process_payment_method(sender_id, 'bank_transfer')
        
        # Order confirmation
        elif payload == "CONFIRM_ORDER":
            confirm_and_create_order(sender_id)
        
        # Cancel order
        elif payload == "CANCEL_ORDER":
            cancel_order(sender_id)
        
        # ============================================
        # VERIFICATION FLOW
        # ============================================
        # ID Verification
        elif payload.startswith("VERIFY_ID_"):
            order_id = payload.split("_")[2]
            start_id_verification(sender_id, int(order_id))
        
        # Upfront Payment
        elif payload.startswith("VERIFY_UPFRONT_"):
            order_id = payload.split("_")[2]
            start_upfront_payment(sender_id, int(order_id))
        
        # Payment method selection for upfront
        elif payload.startswith("PAY_UPFRONT_"):
            parts = payload.split("_")
            payment_method = parts[2].lower()  # gcash, maya, bank
            order_id = parts[3]
            send_payment_instructions(sender_id, int(order_id), payment_method)
    
    except Exception as e:
        logger.error(f"Error in handle_postback: {e}")
        send_message(sender_id, "Sorry, something went wrong. Please try again.")


# ================================================
# MENU & GREETING FUNCTIONS
# ================================================
def send_auto_greeting(sender_id):
    """
    Send welcome greeting to new users
    
    Args:
        sender_id: Facebook user ID
    """
    welcome_text = (
        "👋 Hello! Welcome to QuickSell!\n\n"
        "Your one-stop shop for the latest gadgets and electronics! 🛍️\n\n"
        "Type 'menu' to start shopping!"
    )
    send_message(sender_id, welcome_text)

def send_main_menu(sender_id):
    """
    Display main menu to user
    
    Args:
        sender_id: Facebook user ID
    """
    send_button_template(
        sender_id,
        "🛍️ Welcome to QuickSell!\n\nWhat would you like to explore?",
        [
            {"type": "postback", "title": "📦 Products", "payload": "VIEW_PRODUCTS"},
            {"type": "postback", "title": "🚚 Shipping Info", "payload": "SHIPPING_INFO"},
            {"type": "postback", "title": "🎉 Promos", "payload": "VIEW_PROMOS"}
        ]
    )


# ================================================
# ATTACHMENT HANDLER (Images for Verification)
# ================================================
def handle_attachment(sender_id, attachments):
    """
    Handle image attachments for verification
    
    Args:
        sender_id: Facebook user ID
        attachments: List of attachment objects
    """
    try:
        # Check if user is in verification flow
        if not is_in_conversation(sender_id):
            send_message(sender_id, "Please start an order first. Type 'menu' to browse products.")
            return
        
        state = get_conversation_state(sender_id)
        
        # Extract image URL from attachment
        image_url = None
        for attachment in attachments:
            if attachment.get('type') == 'image':
                image_url = attachment.get('payload', {}).get('url')
                break
        
        if not image_url:
            send_message(sender_id, "❌ Invalid image. Please upload a clear photo.")
            return
        
        # Route to appropriate handler based on state
        if state['state'] == 'AWAITING_ID_UPLOAD':
            order_id = state['data'].get('order_id')
            handle_id_upload(sender_id, order_id, image_url)
        
        elif state['state'] == 'AWAITING_SELFIE_UPLOAD':
            order_id = state['data'].get('order_id')
            handle_selfie_upload(sender_id, order_id, image_url)
        
        elif state['state'] == 'AWAITING_PAYMENT_PROOF':
            order_id = state['data'].get('order_id')
            payment_method = state['data'].get('payment_method')
            amount = state['data'].get('amount')
            handle_payment_proof(sender_id, order_id, image_url, payment_method, amount)
        
        else:
            send_message(sender_id, "I'm not expecting an image right now. Type 'menu' to continue.")
    
    except Exception as e:
        logger.error(f"Error handling attachment: {e}")
        send_message(sender_id, "❌ Error processing image. Please try again.")
