"""
Database service module
Handles all database operations including connection pooling, user management, and chat logging
"""
import mysql.connector
from mysql.connector import pooling
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

# ================================================
# DATABASE CONNECTION POOL
# ================================================
try:
    db_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
    logger.info("✅ Database pool created successfully")
except Exception as e:
    logger.error(f"❌ Database pool error: {e}")
    db_pool = None

def get_db_connection():
    """
    Get connection from pool
    
    Returns:
        Connection object from the pool
    """
    if db_pool is None:
        raise Exception("Database pool is not initialized")
    return db_pool.get_connection()

# ================================================
# USER MANAGEMENT
# ================================================
def get_or_create_user(messenger_id, facebook_name=None):
    """
    Get or create user in database
    
    Args:
        messenger_id: Facebook Messenger user ID
        facebook_name: User's Facebook display name (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE messenger_id = %s", (messenger_id,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute("""
                INSERT INTO users (messenger_id, facebook_name) 
                VALUES (%s, %s)
            """, (messenger_id, facebook_name))
            conn.commit()
            logger.info(f"✅ New user created: {messenger_id}")
        else:
            # Update last interaction timestamp
            cursor.execute("""
                UPDATE users 
                SET last_interaction_at = NOW() 
                WHERE messenger_id = %s
            """, (messenger_id,))
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ================================================
# CHAT LOGGING
# ================================================
def log_chat(user_id, user_message, bot_response, intent=None):
    """
    Log chat interactions for analytics
    
    Args:
        user_id: User's messenger ID
        user_message: Message sent by user
        bot_response: Bot's response
        intent: Detected intent (optional)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_logs (user_id, message_type, user_message, bot_response, intent)
            VALUES (%s, 'text', %s, %s, %s)
        """, (user_id, user_message, bot_response, intent))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging chat: {e}")
    finally:
        cursor.close()
        conn.close()

# ================================================
# CHATBOT REPLIES
# ================================================
def get_keyword_reply(keyword):
    """
    Get predefined reply from chatbot_replies table
    
    Args:
        keyword: The keyword to search for
    
    Returns:
        str: Response text if found, None otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT response FROM chatbot_replies 
            WHERE LOWER(keyword) = %s AND is_active = TRUE
        """, (keyword.lower(),))
        reply = cursor.fetchone()
        return reply['response'] if reply else None
    except Exception as e:
        logger.error(f"Error getting keyword reply: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
