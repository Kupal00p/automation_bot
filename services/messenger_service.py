"""
Messenger service module
Handles all Facebook Messenger API communications
"""
import requests
import logging
from config import PAGE_ACCESS_TOKEN, MAX_BUTTONS_PER_MESSAGE, MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)

MESSENGER_API_URL = "https://graph.facebook.com/v20.0/me/messages"

# ================================================
# BASIC MESSAGING
# ================================================
def send_message(recipient_id, text):
    """
    Send text message to user
    
    Args:
        recipient_id: Facebook user ID
        text: Message text to send
    
    Returns:
        Response object from requests
    """
    url = f"{MESSENGER_API_URL}?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Error sending message: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return None

# ================================================
# MEDIA MESSAGING
# ================================================
def send_image(recipient_id, image_url):
    """
    Send image message with error handling
    
    Args:
        recipient_id: Facebook user ID
        image_url: URL of the image to send
    
    Returns:
        Response object from requests or None on error
    """
    try:
        url = f"{MESSENGER_API_URL}?access_token={PAGE_ACCESS_TOKEN}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            }
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Error sending image: {response.text}")
            return None
        
        return response
    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending image: {image_url}")
        return None
    except Exception as e:
        logger.error(f"Error in send_image: {e}")
        return None

# ================================================
# TEMPLATE MESSAGING
# ================================================
def send_button_template(recipient_id, text, buttons):
    """
    Send button template message
    
    Args:
        recipient_id: Facebook user ID
        text: Template text (max 640 characters)
        buttons: List of button objects (max 3)
    
    Returns:
        Response object from requests
    """
    url = f"{MESSENGER_API_URL}?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text[:MAX_MESSAGE_LENGTH],  # FB character limit
                    "buttons": buttons[:MAX_BUTTONS_PER_MESSAGE]  # Max 3 buttons
                }
            }
        }
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Error sending button template: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Error in send_button_template: {e}")
        return None

# ================================================
# SENDER ACTIONS
# ================================================
def send_typing_indicator(recipient_id):
    """
    Show typing indicator to user
    
    Args:
        recipient_id: Facebook user ID
    """
    url = f"{MESSENGER_API_URL}?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": "typing_on"
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")

def mark_seen(recipient_id):
    """
    Mark message as seen
    
    Args:
        recipient_id: Facebook user ID
    """
    url = f"{MESSENGER_API_URL}?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": "mark_seen"
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error marking seen: {e}")
