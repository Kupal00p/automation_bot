"""
Enterprise-Level Order Processing Service
Handles order lifecycle with state machine pattern and error recovery
"""

import logging
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from database import get_db_connection
from services.order_validator import validate_order

logger = logging.getLogger(__name__)


class OrderState(Enum):
    """Order states in the processing pipeline"""
    CREATED = 'created'
    VALIDATED = 'validated'
    INVENTORY_RESERVED = 'inventory_reserved'
    PAYMENT_PENDING = 'payment_pending'
    PAYMENT_CONFIRMED = 'payment_confirmed'
    CONFIRMED = 'confirmed'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    FAILED = 'failed'


class OrderProcessor:
    """
    Enterprise order processor with state machine
    Handles complete order lifecycle with transactions and rollback
    """
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def create_order(self, order_data: Dict) -> Dict:
        """
        Create and process a new order with full validation
        
        Args:
            order_data: Order data including user_id, items, payment_method, etc.
            
        Returns:
            Dict with order details or error information
        """
        try:
            logger.info(f"📦 Creating order for user {order_data.get('user_id')}")
            
            # Step 1: Validate order
            is_valid, errors, warnings = validate_order(order_data)
            
            if not is_valid:
                logger.error(f"❌ Order validation failed: {errors}")
                return {
                    'success': False,
                    'error': 'Order validation failed',
                    'validation_errors': errors,
                    'warnings': warnings
                }
            
            if warnings:
                logger.warning(f"⚠️ Order warnings: {warnings}")
            
            # Step 2: Start transaction
            self.conn.start_transaction()
            
            try:
                # Step 3: Create order record
                order = self._create_order_record(order_data)
                order_id = order['id']
                
                logger.info(f"✅ Order record created: {order['order_number']}")
                
                # Step 4: Create order items
                self._create_order_items(order_id, order_data.get('items', []))
                
                # Step 5: Reserve inventory
                if not self._reserve_inventory(order_id):
                    raise Exception("Failed to reserve inventory")
                
                # Step 6: Queue notifications
                self._queue_order_notification(order_id, 'order_created')
                
                # Step 7: Add to processing queue
                self._add_to_processing_queue(order_id, 'new_order', priority=3)
                
                # Step 8: Update order state
                self._update_order_state(order_id, OrderState.INVENTORY_RESERVED)
                
                # Commit transaction
                self.conn.commit()
                
                logger.info(f"✅ Order {order['order_number']} created successfully")
                
                return {
                    'success': True,
                    'order': order,
                    'warnings': warnings,
                    'message': 'Order created successfully'
                }
                
            except Exception as e:
                # Rollback on error
                self.conn.rollback()
                logger.error(f"❌ Order creation failed, rolling back: {e}")
                
                # Log error
                if 'order_id' in locals():
                    self._log_order_error(order_id, 'system', str(e), 'critical')
                
                raise
                
        except Exception as e:
            logger.error(f"❌ Order processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create order'
            }
    
    def _create_order_record(self, order_data: Dict) -> Dict:
        """Create the main order record"""
        order_number = self._generate_order_number()
        
        # Calculate remaining balance
        total_amount = Decimal(str(order_data.get('total_amount', 0)))
        upfront_paid = Decimal(str(order_data.get('upfront_paid', 0)))
        remaining_balance = total_amount - upfront_paid
        
        # Prepare order data
        insert_data = {
            'order_number': order_number,
            'user_id': order_data['user_id'],
            'subtotal': order_data.get('subtotal', 0),
            'shipping_fee': order_data.get('shipping_fee', 0),
            'discount_amount': order_data.get('discount_amount', 0),
            'total_amount': total_amount,
            'remaining_balance': remaining_balance,
            'payment_method': order_data.get('payment_method'),
            'payment_status': 'pending',
            'order_status': 'pending',
            'promo_code': order_data.get('promo_code'),
            'notes': json.dumps(order_data.get('shipping_address', {})),
            'verification_required': order_data.get('verification_required', False),
            'verification_status': 'pending' if order_data.get('verification_required') else 'not_required',
            'verification_type': order_data.get('verification_type'),
            'upfront_paid': upfront_paid,
            'order_source': order_data.get('order_source', 'messenger'),
            'ip_address': order_data.get('ip_address'),
            'user_agent': order_data.get('user_agent')
        }
        
        # Insert order
        columns = ', '.join(insert_data.keys())
        placeholders = ', '.join(['%s'] * len(insert_data))
        query = f"INSERT INTO orders ({columns}) VALUES ({placeholders})"
        
        self.cursor.execute(query, list(insert_data.values()))
        order_id = self.cursor.lastrowid
        
        # Fetch created order
        self.cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = self.cursor.fetchone()
        
        # Create initial state history
        self._record_state_change(order_id, None, 'pending', 'system', 'Order created')
        
        # Create order metrics
        self.cursor.execute("""
            INSERT INTO order_metrics (order_id) VALUES (%s)
        """, (order_id,))
        
        return order
    
    def _create_order_items(self, order_id: int, items: List[Dict]):
        """Create order items"""
        for item in items:
            # Get product details
            self.cursor.execute("""
                SELECT name, sku, base_price
                FROM products
                WHERE id = %s
            """, (item['product_id'],))
            
            product = self.cursor.fetchone()
            
            # Get variant details if applicable
            variant_details = None
            unit_price = Decimal(str(product['base_price']))
            
            if item.get('variant_id'):
                self.cursor.execute("""
                    SELECT variant_name, variant_value, price_adjustment
                    FROM product_variants
                    WHERE id = %s
                """, (item['variant_id'],))
                
                variant = self.cursor.fetchone()
                if variant:
                    variant_details = f"{variant['variant_name']}: {variant['variant_value']}"
                    unit_price += Decimal(str(variant['price_adjustment']))
            
            quantity = item['quantity']
            total_price = unit_price * quantity
            
            # Insert order item
            self.cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, variant_id, product_name,
                    variant_details, sku, quantity, unit_price, total_price
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item['product_id'],
                item.get('variant_id'),
                product['name'],
                variant_details,
                product['sku'],
                quantity,
                unit_price,
                total_price
            ))
    
    def _reserve_inventory(self, order_id: int) -> bool:
        """Reserve inventory using stored procedure"""
        try:
            # Call stored procedure to reserve inventory
            self.cursor.callproc('sp_reserve_order_inventory', [order_id, 30])  # 30 min expiry
            
            # Fetch result
            for result in self.cursor.stored_results():
                data = result.fetchone()
                if data and data[0] == 'SUCCESS':
                    logger.info(f"✅ Inventory reserved for order {order_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Inventory reservation failed: {e}")
            self._log_order_error(order_id, 'inventory', str(e), 'critical')
            return False
    
    def _release_inventory(self, order_id: int, reason: str = 'Order cancelled'):
        """Release inventory reservation"""
        try:
            self.cursor.callproc('sp_release_order_inventory', [order_id, reason])
            logger.info(f"✅ Inventory released for order {order_id}: {reason}")
        except Exception as e:
            logger.error(f"❌ Inventory release failed: {e}")
    
    def confirm_order(self, order_id: int, admin_notes: str = None) -> Dict:
        """
        Confirm an order (admin action)
        Commits inventory and moves to processing
        """
        try:
            self.conn.start_transaction()
            
            # Check order status
            self.cursor.execute("""
                SELECT order_status, verification_required, verification_status
                FROM orders
                WHERE id = %s
            """, (order_id,))
            
            order = self.cursor.fetchone()
            
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            if order['order_status'] != 'pending':
                return {'success': False, 'error': f"Order is already {order['order_status']}"}
            
            # Check verification if required
            if order['verification_required'] and order['verification_status'] != 'verified':
                return {'success': False, 'error': 'Order requires verification before confirmation'}
            
            # Commit inventory
            self.cursor.callproc('sp_commit_order_inventory', [order_id])
            
            # Update order status
            self.cursor.execute("""
                UPDATE orders
                SET order_status = 'confirmed',
                    confirmed_at = NOW(),
                    processing_started_at = NOW()
                WHERE id = %s
            """, (order_id,))
            
            # Record state change
            self._record_state_change(order_id, 'pending', 'confirmed', 'admin', admin_notes)
            
            # Queue notification
            self._queue_order_notification(order_id, 'order_confirmed')
            
            # Add to fulfillment queue
            self._add_to_processing_queue(order_id, 'fulfillment', priority=2)
            
            self.conn.commit()
            
            logger.info(f"✅ Order {order_id} confirmed")
            
            return {
                'success': True,
                'message': 'Order confirmed successfully'
            }
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Order confirmation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: int, reason: str, cancelled_by: str = 'admin') -> Dict:
        """
        Cancel an order and release inventory
        """
        try:
            self.conn.start_transaction()
            
            # Get order details
            self.cursor.execute("""
                SELECT order_status, order_number
                FROM orders
                WHERE id = %s
            """, (order_id,))
            
            order = self.cursor.fetchone()
            
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            if order['order_status'] in ['delivered', 'cancelled']:
                return {'success': False, 'error': f"Cannot cancel {order['order_status']} order"}
            
            # Release inventory
            self._release_inventory(order_id, f'Order cancelled: {reason}')
            
            # Update order
            self.cursor.execute("""
                UPDATE orders
                SET order_status = 'cancelled',
                    cancelled_at = NOW(),
                    cancellation_reason = %s
                WHERE id = %s
            """, (reason, order_id))
            
            # Record state change
            self._record_state_change(order_id, order['order_status'], 'cancelled', cancelled_by, reason)
            
            # Queue notification
            self._queue_order_notification(order_id, 'order_cancelled')
            
            self.conn.commit()
            
            logger.info(f"✅ Order {order['order_number']} cancelled: {reason}")
            
            return {
                'success': True,
                'message': 'Order cancelled successfully'
            }
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Order cancellation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_order_state(self, order_id: int, state: OrderState):
        """Update order processing state"""
        self.cursor.execute("""
            UPDATE orders
            SET updated_at = NOW()
            WHERE id = %s
        """, (order_id,))
    
    def _record_state_change(self, order_id: int, from_status: str, to_status: str, 
                            changed_by: str, reason: str = None):
        """Record order state change in history"""
        self.cursor.execute("""
            INSERT INTO order_state_history (
                order_id, from_status, to_status, changed_by, 
                changed_by_type, reason
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (order_id, from_status, to_status, changed_by, 
              'admin' if changed_by == 'admin' else 'system', reason))
    
    def _add_to_processing_queue(self, order_id: int, queue_type: str, priority: int = 5):
        """Add order to processing queue"""
        self.cursor.execute("""
            INSERT INTO order_processing_queue (
                order_id, queue_type, priority, status
            ) VALUES (%s, %s, %s, 'pending')
        """, (order_id, queue_type, priority))
    
    def _queue_order_notification(self, order_id: int, notification_type: str):
        """Queue notification for customer"""
        # Get order and user details
        self.cursor.execute("""
            SELECT o.user_id, o.order_number, o.total_amount,
                   u.messenger_id, u.facebook_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (order_id,))
        
        data = self.cursor.fetchone()
        
        if not data:
            return
        
        # Prepare notification message
        messages = {
            'order_created': f"Your order {data['order_number']} has been received!",
            'order_confirmed': f"Your order {data['order_number']} has been confirmed and is being processed.",
            'order_shipped': f"Your order {data['order_number']} has been shipped!",
            'order_delivered': f"Your order {data['order_number']} has been delivered. Thank you!",
            'order_cancelled': f"Your order {data['order_number']} has been cancelled."
        }
        
        message = messages.get(notification_type, "Order update")
        
        # Queue notification
        self.cursor.execute("""
            INSERT INTO notification_queue (
                order_id, user_id, notification_type, channel,
                recipient, message, status
            ) VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (order_id, data['user_id'], notification_type, 'messenger',
              data['messenger_id'], message))
    
    def _log_order_error(self, order_id: int, error_type: str, error_message: str, 
                        severity: str = 'medium'):
        """Log order error"""
        try:
            self.cursor.execute("""
                INSERT INTO order_errors (
                    order_id, error_type, error_message, severity
                ) VALUES (%s, %s, %s, %s)
            """, (order_id, error_type, error_message, severity))
            
            # Update error count on order
            self.cursor.execute("""
                UPDATE orders
                SET error_count = error_count + 1,
                    last_error = %s
                WHERE id = %s
            """, (error_message, order_id))
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    @staticmethod
    def _generate_order_number() -> str:
        """Generate unique order number"""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = random.randint(10000, 99999)
        return f"ORD-{timestamp}-{random_part}"


# Convenience functions
def create_order(order_data: Dict) -> Dict:
    """Create a new order"""
    with OrderProcessor() as processor:
        return processor.create_order(order_data)


def confirm_order(order_id: int, admin_notes: str = None) -> Dict:
    """Confirm an order"""
    with OrderProcessor() as processor:
        return processor.confirm_order(order_id, admin_notes)


def cancel_order(order_id: int, reason: str, cancelled_by: str = 'admin') -> Dict:
    """Cancel an order"""
    with OrderProcessor() as processor:
        return processor.cancel_order(order_id, reason, cancelled_by)
