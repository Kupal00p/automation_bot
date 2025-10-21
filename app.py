"""
QuickSell Facebook Messenger Bot
Main application entry point
"""
from flask import Flask, request, jsonify, send_from_directory
import logging
import os
from config import VERIFY_TOKEN
from services.db_service import get_or_create_user
from services.handlers_service import handle_user_message, handle_postback, send_auto_greeting, handle_attachment

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Configure Flask session for admin dashboard
app.secret_key = os.getenv('SECRET_KEY', 'quicksell-secret-key-change-in-production')

# Register admin blueprint
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# ================================================
# FAVICON ROUTE
# ================================================
@app.route('/favicon.ico')
def favicon():
    """Serve favicon - prevents 404 errors in browser"""
    return '', 204  # No content response to suppress error

# Track first-time users (in-memory for simplicity, consider Redis for production)
user_first_chat = set()

# Track processed events to prevent duplicates
processed_events = set()

# ================================================
# WEBHOOK ENDPOINT
# ================================================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Webhook endpoint for Facebook Messenger
    - GET: Webhook verification
    - POST: Receive messages and events
    """
    if request.method == "GET":
        # Webhook verification
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified")
            return challenge, 200
        else:
            logger.warning("❌ Verification token mismatch")
            return "Verification token mismatch", 403
    
    elif request.method == "POST":
        # Process incoming messages
        data = request.get_json()
        logger.info(f"📩 Received webhook data")
        
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    # Generate unique event ID to prevent duplicate processing
                    event_id = f"{messaging_event['sender']['id']}_{messaging_event.get('timestamp', '')}"
                    
                    # Skip if already processed
                    if event_id in processed_events:
                        logger.warning(f"⚠️ Skipping duplicate event: {event_id}")
                        continue
                    
                    # Mark event as processed
                    processed_events.add(event_id)
                    
                    # Clean up old events (keep only last 100)
                    if len(processed_events) > 100:
                        processed_events.pop()
                    
                    sender_id = messaging_event["sender"]["id"]
                    
                    # Get or create user in database
                    get_or_create_user(sender_id)
                    
                    # Auto greet first-time users
                    if sender_id not in user_first_chat:
                        send_auto_greeting(sender_id)
                        user_first_chat.add(sender_id)
                        continue
                    
                    # Handle postback (button clicks)
                    if "postback" in messaging_event:
                        payload = messaging_event["postback"]["payload"]
                        handle_postback(sender_id, payload)
                        continue
                    
                    # Ignore echoes and non-message events
                    message = messaging_event.get("message")
                    if not message or message.get("is_echo"):
                        continue
                    
                    # Handle quick reply
                    if "quick_reply" in message:
                        payload = message["quick_reply"]["payload"]
                        handle_postback(sender_id, payload)
                        continue
                    
                    # Handle attachments (images for verification)
                    if "attachments" in message:
                        attachments = message["attachments"]
                        handle_attachment(sender_id, attachments)
                        continue
                    
                    # Handle text message
                    if "text" in message:
                        user_text = message["text"].strip()
                        handle_user_message(sender_id, user_text)
        
        return "EVENT_RECEIVED", 200

# ================================================
# HEALTH CHECK ENDPOINT
# ================================================
@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring
    Checks database connectivity
    """
    from services.db_service import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ================================================
# ROOT ENDPOINT
# ================================================
@app.route("/", methods=["GET"])
def index():
    """
    Root endpoint - bot information
    """
    return jsonify({
        "bot": "QuickSell Messenger Bot",
        "status": "running",
        "version": "1.0.0"
    }), 200

# ================================================
# RUN APPLICATION
# ================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 Starting QuickSell Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
