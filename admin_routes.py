"""
Admin API routes
RESTful API for admin dashboard
"""
from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from functools import wraps
import logging
import os
from werkzeug.utils import secure_filename
from services.admin_service import (
    get_all_orders, get_order_by_id, get_order_by_number,
    update_order_status, confirm_order_by_admin, cancel_order_by_admin,
    get_dashboard_stats, get_recent_activity
)

logger = logging.getLogger(__name__)

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ================================================
# AUTHENTICATION DECORATOR
# ================================================
def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            # Check if this is an API request or page request
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            else:
                # Redirect to login page for browser access
                return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================================================
# AUTH ROUTES
# ================================================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page - Simple hardcoded authentication"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Simple hardcoded check
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            logger.info(f"✅ Admin logged in: {username}")
            return jsonify({'success': True})
        else:
            logger.warning(f"❌ Failed login attempt: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('admin/login.html')

@admin_bp.route('/logout', methods=['POST'])
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    logger.info("Admin logged out")
    return jsonify({'success': True})

# ================================================
# DASHBOARD ROUTES
# ================================================
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard page"""
    return render_template('admin/dashboard.html')

# ================================================
# API ENDPOINTS
# ================================================
@admin_bp.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    """Get dashboard statistics"""
    try:
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
        # Return empty stats instead of error
        return jsonify({
            'total_orders': 0,
            'total_revenue': 0,
            'pending_orders': 0,
            'active_users': 0,
            'new_customers': 0,
            'repeat_customers': 0,
            'avg_order_value': 0,
            'weekly_sales': [0, 0, 0, 0, 0, 0, 0],
            'order_status_counts': [0, 0, 0, 0, 0],
            'monthly_revenue': [],
            'top_products': []
        })

@admin_bp.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    """Get orders list with filters"""
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    orders = get_all_orders(status=status, limit=limit, offset=offset)
    
    # Convert datetime to string for JSON serialization
    for order in orders:
        order['created_at'] = order['created_at'].isoformat() if order.get('created_at') else None
        for item in order.get('items', []):
            if 'created_at' in item and item['created_at']:
                item['created_at'] = item['created_at'].isoformat()
    
    return jsonify({'orders': orders, 'count': len(orders)})

@admin_bp.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def api_order_detail(order_id):
    """Get single order details"""
    try:
        order = get_order_by_id(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Convert datetime to string for main order
        datetime_fields = ['created_at', 'confirmed_at', 'shipped_at', 'delivered_at', 
                          'cancelled_at', 'updated_at', 'verification_expires_at']
        
        for field in datetime_fields:
            if order.get(field):
                order[field] = order[field].isoformat()
        
        # Convert datetime for order items
        for item in order.get('items', []):
            if 'created_at' in item and item['created_at']:
                item['created_at'] = item['created_at'].isoformat()
        
        # Convert datetime for verification
        if order.get('verification'):
            verification = order['verification']
            for field in ['submitted_at', 'reviewed_at', 'expires_at']:
                if verification.get(field):
                    verification[field] = verification[field].isoformat()
        
        return jsonify(order)
        
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@admin_bp.route('/api/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
def api_confirm_order(order_id):
    """Confirm order - main endpoint"""
    try:
        logger.info(f"📥 Received confirm request for order_id: {order_id}")
        data = request.get_json() or {}
        admin_notes = data.get('notes')
        
        success = confirm_order_by_admin(order_id, admin_notes)
        
        if success:
            logger.info(f"✅ Order {order_id} confirmed by admin via API")
            return jsonify({'success': True, 'message': 'Order confirmed successfully'})
        else:
            logger.error(f"❌ Failed to confirm order {order_id} - check admin_service logs")
            return jsonify({'error': 'Failed to confirm order. Check server logs for details.'}), 500
    except Exception as e:
        logger.error(f"❌ Exception in api_confirm_order: {e}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@admin_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def api_cancel_order(order_id):
    """Cancel order"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Cancelled by admin')
    
    success = cancel_order_by_admin(order_id, reason)
    
    if success:
        logger.info(f"❌ Order {order_id} cancelled by admin")
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
    else:
        return jsonify({'error': 'Failed to cancel order'}), 500

@admin_bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def api_update_status(order_id):
    """Update order status"""
    data = request.get_json()
    new_status = data.get('status')
    notify = data.get('notify_customer', True)
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    success = update_order_status(order_id, new_status, notify_customer=notify)
    
    if success:
        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    else:
        return jsonify({'error': 'Failed to update status'}), 500

@admin_bp.route('/api/activity', methods=['GET'])
@login_required
def api_activity():
    """Get recent activity"""
    limit = int(request.args.get('limit', 10))
    activity = get_recent_activity(limit=limit)
    
    # Convert datetime
    for item in activity:
        if item.get('created_at'):
            item['created_at'] = item['created_at'].isoformat()
    
    return jsonify({'activity': activity})

# ================================================
# UTILITY ROUTES
# ================================================
@admin_bp.route('/api/search', methods=['GET'])
@login_required
def api_search():
    """Search orders by order number"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    order = get_order_by_number(query)
    
    if order:
        # Convert datetime
        if order.get('created_at'):
            order['created_at'] = order['created_at'].isoformat()
        
        return jsonify({'order': order})
    else:
        return jsonify({'error': 'Order not found'}), 404

# ================================================
# VERIFICATION ROUTES
# ================================================
@admin_bp.route('/api/verifications/pending', methods=['GET'])
@login_required
def api_pending_verifications():
    """Get all pending verifications"""
    try:
        from services.db_service import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ov.id, ov.order_id, ov.verification_type,
                ov.verification_status, ov.id_image_url, ov.selfie_image_url,
                ov.upfront_amount, ov.payment_proof_url, ov.payment_method,
                ov.submitted_at, ov.expires_at,
                o.order_number, o.total_amount,
                u.facebook_name, u.phone, u.messenger_id
            FROM order_verifications ov
            JOIN orders o ON ov.order_id = o.id
            JOIN users u ON ov.user_id = u.id
            WHERE ov.verification_status IN ('pending', 'under_review')
            ORDER BY ov.submitted_at DESC
        """)
        
        verifications = cursor.fetchall()
        
        # Convert datetime to string
        for v in verifications:
            if v.get('submitted_at'):
                v['submitted_at'] = v['submitted_at'].isoformat()
            if v.get('expires_at'):
                v['expires_at'] = v['expires_at'].isoformat()
        
        return jsonify({'verifications': verifications, 'count': len(verifications)})
        
    except Exception as e:
        logger.error(f"Error getting pending verifications: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/api/verifications/<int:verification_id>', methods=['GET'])
@login_required
def api_verification_detail(verification_id):
    """Get single verification details"""
    try:
        from services.db_service import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ov.*,
                o.order_number, o.total_amount, o.payment_method as order_payment_method,
                o.notes as order_notes,
                u.facebook_name, u.phone, u.email, u.messenger_id
            FROM order_verifications ov
            JOIN orders o ON ov.order_id = o.id
            JOIN users u ON ov.user_id = u.id
            WHERE ov.id = %s
        """, (verification_id,))
        
        verification = cursor.fetchone()
        
        if not verification:
            return jsonify({'error': 'Verification not found'}), 404
        
        # Convert datetime
        if verification.get('submitted_at'):
            verification['submitted_at'] = verification['submitted_at'].isoformat()
        if verification.get('reviewed_at'):
            verification['reviewed_at'] = verification['reviewed_at'].isoformat()
        if verification.get('expires_at'):
            verification['expires_at'] = verification['expires_at'].isoformat()
        
        return jsonify(verification)
        
    except Exception as e:
        logger.error(f"Error getting verification {verification_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/api/verifications/<int:order_id>/approve', methods=['POST'])
@login_required
def api_approve_verification(order_id):
    """Approve verification"""
    try:
        from services.verification_service import approve_verification
        
        admin_id = session.get('admin_id')  # You may need to add this to session on login
        
        success = approve_verification(order_id, admin_id)
        
        if success:
            logger.info(f"✅ Verification approved for order {order_id} by admin")
            return jsonify({'success': True, 'message': 'Verification approved successfully'})
        else:
            return jsonify({'error': 'Failed to approve verification'}), 500
            
    except Exception as e:
        logger.error(f"Error approving verification: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/verifications/<int:order_id>/reject', methods=['POST'])
@login_required
def api_reject_verification(order_id):
    """Reject verification"""
    try:
        from services.verification_service import reject_verification
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Verification rejected by admin')
        admin_id = session.get('admin_id')
        
        success = reject_verification(order_id, reason, admin_id)
        
        if success:
            logger.info(f"❌ Verification rejected for order {order_id}")
            return jsonify({'success': True, 'message': 'Verification rejected'})
        else:
            return jsonify({'error': 'Failed to reject verification'}), 500
            
    except Exception as e:
        logger.error(f"Error rejecting verification: {e}")
        return jsonify({'error': str(e)}), 500
