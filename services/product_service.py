"""
Product service module
Handles all product-related operations including categories, products, and promotions
"""
import logging
import json
import time
from services.db_service import get_db_connection
from services.messenger_service import send_message, send_button_template, send_image, send_typing_indicator
from config import PRODUCTS_PER_PAGE, MAX_IMAGES_PER_PRODUCT

logger = logging.getLogger(__name__)

# Track user pagination for categories
user_pagination = {}  # {user_id: {'category': 'laptops', 'page': 0}}

# ================================================
# CATEGORIES
# ================================================
def get_categories():
    """
    Get all active categories
    
    Returns:
        list: List of category dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, slug, icon_emoji 
            FROM categories 
            WHERE is_active = TRUE 
            ORDER BY display_order
            LIMIT 7
        """)
        categories = cursor.fetchall()
        return categories
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def show_categories(sender_id):
    """
    Display categories to user
    
    Args:
        sender_id: Facebook user ID
    """
    categories = get_categories()
    
    if not categories:
        send_message(sender_id, "No categories available at the moment.")
        return
    
    # Split into two messages (3 + 4) due to button limit
    buttons1 = []
    for cat in categories[:3]:
        emoji = cat.get('icon_emoji', '📦')
        buttons1.append({
            "type": "postback",
            "title": f"{emoji} {cat['name']}",
            "payload": f"CATEGORY_{cat['slug']}"
        })
    
    send_button_template(sender_id, "📦 Select a product category:", buttons1)
    
    # Second message with remaining categories
    if len(categories) > 3:
        buttons2 = []
        for cat in categories[3:]:
            emoji = cat.get('icon_emoji', '📦')
            buttons2.append({
                "type": "postback",
                "title": f"{emoji} {cat['name']}",
                "payload": f"CATEGORY_{cat['slug']}"
            })
        buttons2.append({"type": "postback", "title": "🔙 Back", "payload": "MAIN_MENU"})
        send_button_template(sender_id, "More categories:", buttons2)

# ================================================
# PRODUCTS
# ================================================
def show_products_page(sender_id, category_slug, page):
    """
    Display products with pagination
    
    Args:
        sender_id: Facebook user ID
        category_slug: Category slug identifier
        page: Page number (0-indexed)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get category info
        cursor.execute("SELECT id, name FROM categories WHERE slug = %s", (category_slug,))
        category = cursor.fetchone()
        
        if not category:
            send_message(sender_id, "Category not found.")
            return
        
        # Get products
        cursor.execute("""
            SELECT p.id, p.name, p.base_price, p.stock_quantity
            FROM products p
            WHERE p.category_id = %s AND p.status = 'active'
            ORDER BY p.is_featured DESC, p.sales_count DESC
        """, (category['id'],))
        all_products = cursor.fetchall()
        
        total_products = len(all_products)
        if total_products == 0:
            send_button_template(
                sender_id,
                f"No products available in {category['name']} right now.",
                [{"type": "postback", "title": "🔙 Back", "payload": "VIEW_PRODUCTS"}]
            )
            return
        
        # Pagination
        products_per_page = PRODUCTS_PER_PAGE
        start_idx = page * products_per_page
        end_idx = start_idx + products_per_page
        products_page = all_products[start_idx:end_idx]
        total_pages = (total_products + products_per_page - 1) // products_per_page
        current_page = page + 1
        
        # Product buttons
        buttons = []
        for p in products_page:
            title = p['name'][:18] if len(p['name']) > 18 else p['name']
            buttons.append({
                "type": "postback",
                "title": f"{title}",
                "payload": f"PRODUCT_{p['id']}"
            })
        
        header = f"📦 {category['name']}\nPage {current_page} of {total_pages}"
        send_button_template(sender_id, header, buttons)
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append({"type": "postback", "title": "⬅️ Previous", "payload": "SHOW_PREVIOUS"})
        if end_idx < total_products:
            nav_buttons.append({"type": "postback", "title": "➡️ Next", "payload": "SHOW_MORE"})
        nav_buttons.append({"type": "postback", "title": "🔙 Back", "payload": "VIEW_PRODUCTS"})
        
        send_button_template(sender_id, "Navigate:", nav_buttons)
        
    except Exception as e:
        logger.error(f"Error in show_products_page: {e}")
        send_message(sender_id, "Error loading products.")
    finally:
        cursor.close()
        conn.close()

def show_product_details(sender_id, product_id):
    """
    Show detailed product information with images
    
    Args:
        sender_id: Facebook user ID
        product_id: Product ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get product with brand and category
        cursor.execute("""
            SELECT p.*, b.name as brand_name, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.status = 'active'
        """, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            send_message(sender_id, "Sorry, this product is not available.")
            return
        
        # Get product images
        cursor.execute("""
            SELECT image_url FROM product_images 
            WHERE product_id = %s 
            ORDER BY is_primary DESC, display_order 
            LIMIT %s
        """, (product_id, MAX_IMAGES_PER_PRODUCT))
        images = cursor.fetchall()
        
        # Send typing indicator for better UX
        send_typing_indicator(sender_id)
        
        # Send images if available (limit to 3 images to avoid flooding)
        if images:
            # Limit to first 3 images only
            images_to_send = images[:3]
            
            for idx, img in enumerate(images_to_send):
                try:
                    send_image(sender_id, img['image_url'])
                    time.sleep(0.5)  # Delay between images
                except Exception as img_error:
                    logger.error(f"Error sending image {idx+1}: {img_error}")
                    continue
            
            # Small pause before sending details
            time.sleep(0.5)
        else:
            # No images available - log warning
            logger.warning(f"No images found for product_id: {product_id}")
        
        # Build product details message
        details = (
            f"📱 {product['name']}\n"
            f"🏷️ Brand: {product['brand_name']}\n"
            f"📂 Category: {product['category_name']}\n\n"
            f"💵 Price: ₱{product['base_price']:,.2f}\n"
            f"📦 Stock: {product['stock_quantity']} available\n\n"
        )
        
        # Add description (truncate if too long)
        if product['description']:
            desc = product['description'][:250]
            if len(product['description']) > 250:
                desc += "..."
            details += f"📝 {desc}\n\n"
        
        # Add specifications if available
        if product['specifications']:
            try:
                specs = json.loads(product['specifications']) if isinstance(product['specifications'], str) else product['specifications']
                details += "⚙️ Specifications:\n"
                spec_count = 0
                for key, value in specs.items():
                    if spec_count < 4:  # Limit to 4 specs to avoid too long message
                        details += f" • {key.replace('_', ' ').title()}: {value}\n"
                        spec_count += 1
                if len(specs) > 4:
                    details += f" • +{len(specs) - 4} more specs\n"
                details += "\n"
            except:
                pass
        
        # Add rating if available
        if product.get('average_rating') and product['average_rating'] > 0:
            stars = "⭐" * int(product['average_rating'])
            half_star = "⭐" if (product['average_rating'] % 1) >= 0.5 else ""
            details += f"{stars}{half_star} {product['average_rating']:.1f}/5.0"
            if product.get('review_count'):
                details += f" ({product['review_count']} reviews)"
            details += "\n\n"
        
        # Stock status indicator
        if product['stock_quantity'] <= 5:
            details += "⚠️ Low stock! Order now!\n\n"
        elif product['stock_quantity'] > 50:
            details += "✅ In stock - ready to ship!\n\n"
        
        # Action buttons
        buttons = [
            {"type": "postback", "title": "🛒 Order Now", "payload": f"ORDER_{product_id}"},
            {"type": "postback", "title": "🔙 Back", "payload": f"CATEGORY_{product['category_slug']}"}
        ]
        
        # Send the details message with buttons
        send_button_template(sender_id, details[:640], buttons)  # FB 640 char limit
        
        # Update view count
        cursor.execute("UPDATE products SET view_count = view_count + 1 WHERE id = %s", (product_id,))
        conn.commit()
        
        logger.info(f"✅ Displayed product {product_id} to user {sender_id}")
        
    except Exception as e:
        logger.error(f"Error in show_product_details: {e}")
        send_message(sender_id, "Sorry, something went wrong loading the product. Please try again or type 'menu'.")
    finally:
        cursor.close()
        conn.close()

# ================================================
# PROMOTIONS
# ================================================
def get_active_promos():
    """
    Get all active promotions
    
    Returns:
        list: List of promo dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM promos 
            WHERE is_active = TRUE 
            AND NOW() BETWEEN start_date AND end_date
            ORDER BY created_at DESC
        """)
        promos = cursor.fetchall()
        return promos
    except Exception as e:
        logger.error(f"Error getting promos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def show_promos(sender_id):
    """
    Display active promotions to user
    
    Args:
        sender_id: Facebook user ID
    """
    promos = get_active_promos()
    
    if promos:
        promo_text = "🎉 Current Promos & Deals:\n\n"
        for promo in promos:
            promo_text += f"✨ {promo['title']}\n{promo['description']}\n"
            if promo.get('promo_code'):
                promo_text += f"Code: {promo['promo_code']}\n"
            promo_text += "\n"
        
        send_button_template(
            sender_id,
            promo_text[:640],  # FB limit
            [
                {"type": "postback", "title": "📦 View Products", "payload": "VIEW_PRODUCTS"},
                {"type": "postback", "title": "🔙 Back", "payload": "MAIN_MENU"}
            ]
        )
    else:
        send_button_template(
            sender_id,
            "No active promos at the moment. Check back soon!",
            [{"type": "postback", "title": "🔙 Back", "payload": "MAIN_MENU"}]
        )

# ================================================
# SHIPPING INFO
# ================================================
def show_shipping_info(sender_id):
    """
    Display shipping information to user
    
    Args:
        sender_id: Facebook user ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM shipping_zones WHERE is_active = TRUE")
        zones = cursor.fetchall()
        
        shipping_text = "🚚 Shipping Fees:\n\n"
        for zone in zones:
            shipping_text += f"📍 {zone['zone_name']}: ₱{zone['base_fee']:.0f}\n"
            if zone.get('free_shipping_threshold'):
                shipping_text += f"   Free shipping ≥ ₱{zone['free_shipping_threshold']:.0f}\n"
        
        send_button_template(
            sender_id,
            shipping_text,
            [{"type": "postback", "title": "🔙 Back to Menu", "payload": "MAIN_MENU"}]
        )
    except Exception as e:
        logger.error(f"Error showing shipping info: {e}")
        send_message(sender_id, "Error loading shipping information.")
    finally:
        cursor.close()
        conn.close()
