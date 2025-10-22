"""
Enterprise-Level Order Validation Service
Validates all aspects of an order before processing
"""

import logging
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from datetime import datetime
from database import get_db_connection

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, message: str, code: str = None):
        self.field = field
        self.message = message
        self.code = code or 'VALIDATION_ERROR'
        super().__init__(f"{field}: {message}")


class OrderValidator:
    """Comprehensive order validation"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
        
    def validate_order(self, order_data: Dict) -> Tuple[bool, List[Dict], List[str]]:
        """
        Validate complete order
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # Run all validations
            self._validate_user(order_data.get('user_id'))
            self._validate_items(order_data.get('items', []))
            self._validate_amounts(order_data)
            self._validate_payment_method(order_data.get('payment_method'))
            self._validate_shipping(order_data.get('shipping_address'))
            self._validate_inventory(order_data.get('items', []))
            self._validate_promo_code(order_data.get('promo_code'), order_data)
            self._validate_verification_requirements(order_data)
            
            # Convert errors to dict format
            error_list = [
                {
                    'field': e.field,
                    'message': e.message,
                    'code': e.code
                } for e in self.errors
            ]
            
            is_valid = len(self.errors) == 0
            
            if is_valid:
                logger.info(f"✅ Order validation passed for user {order_data.get('user_id')}")
            else:
                logger.warning(f"❌ Order validation failed: {len(self.errors)} errors")
                
            return is_valid, error_list, self.warnings
            
        except Exception as e:
            logger.error(f"Validation exception: {e}", exc_info=True)
            return False, [{'field': 'system', 'message': str(e), 'code': 'SYSTEM_ERROR'}], []
    
    def _validate_user(self, user_id: int):
        """Validate user exists and is active"""
        if not user_id:
            self.errors.append(ValidationError('user_id', 'User ID is required', 'USER_REQUIRED'))
            return
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, account_status, total_orders, total_spent
                FROM users WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if not user:
                self.errors.append(ValidationError('user_id', 'User not found', 'USER_NOT_FOUND'))
                return
                
            if user['account_status'] not in ['active']:
                self.errors.append(
                    ValidationError('user_id', f"User account is {user['account_status']}", 'USER_INACTIVE')
                )
            
            # Check if user has too many pending orders
            cursor.execute("""
                SELECT COUNT(*) as pending_count
                FROM orders
                WHERE user_id = %s AND order_status = 'pending'
            """, (user_id,))
            
            result = cursor.fetchone()
            if result['pending_count'] >= 5:
                self.warnings.append('User has multiple pending orders')
                
        except Exception as e:
            logger.error(f"User validation error: {e}")
            self.errors.append(ValidationError('user_id', 'Failed to validate user', 'USER_CHECK_FAILED'))
        finally:
            cursor.close()
            conn.close()  # Already using putconn
    
    def _validate_items(self, items: List[Dict]):
        """Validate order items"""
        if not items or len(items) == 0:
            self.errors.append(ValidationError('items', 'Order must have at least one item', 'ITEMS_REQUIRED'))
            return
        
        if len(items) > 50:
            self.errors.append(ValidationError('items', 'Order cannot have more than 50 items', 'TOO_MANY_ITEMS'))
            
        for idx, item in enumerate(items):
            self._validate_single_item(item, idx)
    
    def _validate_single_item(self, item: Dict, index: int):
        """Validate a single order item"""
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        
        if not product_id:
            self.errors.append(
                ValidationError(f'items[{index}].product_id', 'Product ID is required', 'PRODUCT_REQUIRED')
            )
            return
        
        if quantity <= 0:
            self.errors.append(
                ValidationError(f'items[{index}].quantity', 'Quantity must be positive', 'INVALID_QUANTITY')
            )
            return
        
        if quantity > 100:
            self.errors.append(
                ValidationError(f'items[{index}].quantity', 'Quantity cannot exceed 100 per item', 'QUANTITY_LIMIT')
            )
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, name, status, base_price, stock_quantity
                FROM products
                WHERE id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            
            if not product:
                self.errors.append(
                    ValidationError(f'items[{index}].product_id', 'Product not found', 'PRODUCT_NOT_FOUND')
                )
                return
            
            if product['status'] != 'active':
                self.errors.append(
                    ValidationError(
                        f'items[{index}].product_id', 
                        f"Product '{product['name']}' is not available", 
                        'PRODUCT_UNAVAILABLE'
                    )
                )
            
            # Validate variant if specified
            variant_id = item.get('variant_id')
            if variant_id:
                cursor.execute("""
                    SELECT id, variant_name, variant_value, stock_quantity, is_available
                    FROM product_variants
                    WHERE id = %s AND product_id = %s
                """, (variant_id, product_id))
                
                variant = cursor.fetchone()
                if not variant:
                    self.errors.append(
                        ValidationError(f'items[{index}].variant_id', 'Variant not found', 'VARIANT_NOT_FOUND')
                    )
                elif not variant['is_available']:
                    self.errors.append(
                        ValidationError(
                            f'items[{index}].variant_id', 
                            f"Variant {variant['variant_name']}: {variant['variant_value']} is not available", 
                            'VARIANT_UNAVAILABLE'
                        )
                    )
                    
        except Exception as e:
            logger.error(f"Item validation error: {e}")
            self.errors.append(
                ValidationError(f'items[{index}]', 'Failed to validate item', 'ITEM_CHECK_FAILED')
            )
        finally:
            cursor.close()
            conn.close()  # Already using putconn
    
    def _validate_amounts(self, order_data: Dict):
        """Validate order amounts"""
        subtotal = Decimal(str(order_data.get('subtotal', 0)))
        shipping_fee = Decimal(str(order_data.get('shipping_fee', 0)))
        discount = Decimal(str(order_data.get('discount_amount', 0)))
        total = Decimal(str(order_data.get('total_amount', 0)))
        
        if subtotal <= 0:
            self.errors.append(ValidationError('subtotal', 'Subtotal must be positive', 'INVALID_SUBTOTAL'))
        
        if shipping_fee < 0:
            self.errors.append(ValidationError('shipping_fee', 'Shipping fee cannot be negative', 'INVALID_SHIPPING'))
        
        if discount < 0:
            self.errors.append(ValidationError('discount_amount', 'Discount cannot be negative', 'INVALID_DISCOUNT'))
        
        if total <= 0:
            self.errors.append(ValidationError('total_amount', 'Total amount must be positive', 'INVALID_TOTAL'))
        
        # Validate calculation
        expected_total = subtotal + shipping_fee - discount
        if abs(expected_total - total) > Decimal('0.01'):  # Allow 1 cent rounding difference
            self.errors.append(
                ValidationError(
                    'total_amount', 
                    f'Total amount mismatch. Expected: {expected_total}, Got: {total}', 
                    'AMOUNT_MISMATCH'
                )
            )
        
        # Validate against maximum order value
        if total > Decimal('500000'):  # 500k PHP limit
            self.warnings.append('Order exceeds maximum value of ₱500,000 - requires special approval')
    
    def _validate_payment_method(self, payment_method: str):
        """Validate payment method"""
        valid_methods = ['cod', 'gcash', 'bank_transfer', 'credit_card', 'paymaya']
        
        if not payment_method:
            self.errors.append(ValidationError('payment_method', 'Payment method is required', 'PAYMENT_REQUIRED'))
            return
        
        if payment_method not in valid_methods:
            self.errors.append(
                ValidationError('payment_method', f'Invalid payment method: {payment_method}', 'INVALID_PAYMENT')
            )
    
    def _validate_shipping(self, address: Dict):
        """Validate shipping address"""
        if not address:
            self.errors.append(ValidationError('shipping_address', 'Shipping address is required', 'ADDRESS_REQUIRED'))
            return
        
        required_fields = ['recipient_name', 'phone', 'address', 'city', 'province']
        
        for field in required_fields:
            if not address.get(field):
                self.errors.append(
                    ValidationError(
                        f'shipping_address.{field}', 
                        f'{field.replace("_", " ").title()} is required', 
                        'ADDRESS_INCOMPLETE'
                    )
                )
        
        # Validate phone format
        phone = address.get('phone', '')
        if phone and not self._is_valid_phone(phone):
            self.errors.append(
                ValidationError('shipping_address.phone', 'Invalid phone number format', 'INVALID_PHONE')
            )
    
    def _validate_inventory(self, items: List[Dict]):
        """Validate inventory availability"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            for idx, item in enumerate(items):
                product_id = item.get('product_id')
                variant_id = item.get('variant_id')
                quantity = item.get('quantity', 0)
                
                if not product_id:
                    continue
                
                # Check product stock
                if variant_id:
                    cursor.execute("""
                        SELECT stock_quantity, variant_name, variant_value
                        FROM product_variants
                        WHERE id = %s
                    """, (variant_id,))
                    stock_data = cursor.fetchone()
                    item_name = f"{stock_data['variant_name']}: {stock_data['variant_value']}" if stock_data else 'Variant'
                else:
                    cursor.execute("""
                        SELECT stock_quantity, name
                        FROM products
                        WHERE id = %s
                    """, (product_id,))
                    stock_data = cursor.fetchone()
                    item_name = stock_data['name'] if stock_data else 'Product'
                
                if not stock_data:
                    continue
                
                available_stock = stock_data['stock_quantity']
                
                if available_stock < quantity:
                    self.errors.append(
                        ValidationError(
                            f'items[{idx}].quantity',
                            f'Insufficient stock for {item_name}. Available: {available_stock}, Requested: {quantity}',
                            'INSUFFICIENT_STOCK'
                        )
                    )
                elif available_stock < quantity + 5:  # Low stock warning
                    self.warnings.append(f'Low stock for {item_name}: Only {available_stock} remaining')
                    
        except Exception as e:
            logger.error(f"Inventory validation error: {e}")
            self.errors.append(
                ValidationError('inventory', 'Failed to validate inventory', 'INVENTORY_CHECK_FAILED')
            )
        finally:
            cursor.close()
            conn.close()  # Already using putconn
    
    def _validate_promo_code(self, promo_code: Optional[str], order_data: Dict):
        """Validate promo code if provided"""
        if not promo_code:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM promos
                WHERE promo_code = %s AND is_active = TRUE
            """, (promo_code,))
            
            promo = cursor.fetchone()
            
            if not promo:
                self.errors.append(
                    ValidationError('promo_code', 'Invalid or inactive promo code', 'INVALID_PROMO')
                )
                return
            
            # Check date validity
            now = datetime.now()
            if promo['start_date'] > now:
                self.errors.append(
                    ValidationError('promo_code', 'Promo code is not yet active', 'PROMO_NOT_STARTED')
                )
            elif promo['end_date'] < now:
                self.errors.append(
                    ValidationError('promo_code', 'Promo code has expired', 'PROMO_EXPIRED')
                )
            
            # Check usage limit
            if promo['usage_limit'] and promo['usage_count'] >= promo['usage_limit']:
                self.errors.append(
                    ValidationError('promo_code', 'Promo code usage limit reached', 'PROMO_LIMIT_REACHED')
                )
            
            # Check minimum purchase
            subtotal = Decimal(str(order_data.get('subtotal', 0)))
            if promo['min_purchase_amount'] and subtotal < promo['min_purchase_amount']:
                self.errors.append(
                    ValidationError(
                        'promo_code',
                        f"Minimum purchase of ₱{promo['min_purchase_amount']} required for this promo",
                        'PROMO_MIN_NOT_MET'
                    )
                )
                
        except Exception as e:
            logger.error(f"Promo validation error: {e}")
            self.warnings.append('Could not validate promo code')
        finally:
            cursor.close()
            conn.close()  # Already using putconn
    
    def _validate_verification_requirements(self, order_data: Dict):
        """Determine if order requires verification"""
        total_amount = Decimal(str(order_data.get('total_amount', 0)))
        payment_method = order_data.get('payment_method')
        user_id = order_data.get('user_id')
        
        # High-value COD orders require verification
        if payment_method == 'cod' and total_amount > Decimal('50000'):
            order_data['verification_required'] = True
            order_data['verification_type'] = 'id_verification'
            self.warnings.append('This order requires ID verification due to high value COD payment')
        
        # Check if user is trusted
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT verification_skip_enabled
                FROM trusted_buyers
                WHERE user_id = %s
            """, (user_id,))
            
            trusted = cursor.fetchone()
            if trusted and trusted['verification_skip_enabled']:
                order_data['verification_required'] = False
                self.warnings.append('Verification skipped for trusted buyer')
                
        except Exception as e:
            logger.error(f"Verification check error: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()  # Already using putconn
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate Philippine phone number format"""
        import re
        # Allow formats: 09XXXXXXXXX, +639XXXXXXXXX, 639XXXXXXXXX
        pattern = r'^(09|\+639|639)\d{9}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


def validate_order(order_data: Dict) -> Tuple[bool, List[Dict], List[str]]:
    """
    Convenience function for order validation
    
    Args:
        order_data: Order data dictionary
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = OrderValidator()
    return validator.validate_order(order_data)
