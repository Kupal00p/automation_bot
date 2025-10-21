## 🗄️ QuickSell V2.0 - Complete Database Rewrite

### Complete Enterprise-Grade Database from Scratch

---

## 📦 What's Included

### **Part 1: Core Schema** (`quicksell_complete_v2.sql`)
- **27 tables** with full enterprise features built-in
- **50+ indexes** for optimal performance
- **Complete order management** system
- **Inventory tracking** with reservations
- **Verification system** integrated
- **Error logging** and metrics
- **Notification queuing**
- **Full audit trail**

### **Part 2: Automation** (`quicksell_automation_v2.sql`)
- **3 triggers** for automatic actions
- **4 stored procedures** for complex operations
- **5 views** for reporting
- **3 scheduled events** for maintenance

---

## 🚀 Quick Setup (10 minutes)

### **Step 1: Drop Old Database (if exists)**

```bash
mysql -u root -p
```

```sql
DROP DATABASE IF EXISTS quicksell_chatbot;
```

### **Step 2: Run Core Schema**

```bash
mysql -u root -p < database/quicksell_complete_v2.sql
```

**What this creates:**
```
✅ Database: quicksell_chatbot
✅ Tables: 27 total
  - Core: 10 tables (users, products, categories, etc.)
  - Orders: 7 tables (orders, items, history, queue, etc.)
  - Verification: 3 tables
  - Supporting: 7 tables (cart, wishlist, notifications, etc.)
✅ Indexes: 50+ strategic indexes
✅ Foreign Keys: Full referential integrity
```

### **Step 3: Run Automation Layer**

```bash
mysql -u root -p < database/quicksell_automation_v2.sql
```

**What this creates:**
```
✅ Triggers: 3 automatic actions
  - Auto-record order status changes
  - Auto-update user stats on delivery
  - Auto-log inventory changes
  
✅ Procedures: 4 stored procedures
  - sp_reserve_order_inventory
  - sp_release_order_inventory  
  - sp_commit_order_inventory
  - sp_get_order_details
  
✅ Views: 5 reporting views
  - vw_orders_detailed
  - vw_pending_orders
  - vw_inventory_status
  - vw_daily_metrics
  - vw_customer_ltv
  
✅ Events: 3 scheduled jobs
  - Cleanup expired reservations (every 5 min)
  - Cleanup old queue items (daily)
  - Update daily analytics (midnight)
```

### **Step 4: Verify Installation**

```sql
USE quicksell_chatbot;

-- Check tables
SHOW TABLES;
-- Should show 27 tables

-- Check triggers
SHOW TRIGGERS;
-- Should show 3 triggers

-- Check procedures
SHOW PROCEDURE STATUS WHERE Db = 'quicksell_chatbot';
-- Should show 4 procedures

-- Check views
SHOW FULL TABLES WHERE Table_type = 'VIEW';
-- Should show 5 views

-- Check events
SHOW EVENTS;
-- Should show 3 events
```

---

## 📊 Database Structure

### **Core Tables (10)**
```
categories          - Product categories
brands              - Product brands
users               - Customers
admin_users         - Admin accounts
products            - Products catalog
product_images      - Product photos
product_variants    - Product variations
user_addresses      - Customer addresses
promos              - Promo codes
promo_products      - Promo-product links
```

### **Order Tables (7)**
```
orders                    - Main orders
order_items               - Order line items
order_state_history       - Status change audit
order_processing_queue    - Async processing queue
inventory_reservations    - Stock reservations
order_errors              - Error tracking
order_metrics             - Performance metrics
```

### **Verification Tables (3)**
```
order_verifications       - ID/Payment verification
user_verification_history - User verification stats
trusted_buyers            - Verified trusted customers
```

### **Supporting Tables (7)**
```
cart_items          - Shopping carts
wishlists           - Customer wishlists
product_reviews     - Product reviews
notification_queue  - Notification scheduler
inventory_logs      - Inventory movements
chatbot_replies     - Bot responses
chat_logs           - Conversation logs
shipping_zones      - Shipping rates
analytics_daily     - Daily analytics
```

---

## 🎯 Key Improvements Over V1

| Feature | V1 | V2 |
|---------|----|----|
| **Tables** | 20 | 27 |
| **Indexes** | 15 | 50+ |
| **Triggers** | 0 | 3 |
| **Procedures** | 0 | 4 |
| **Views** | 0 | 5 |
| **Events** | 0 | 3 |
| **Order Tracking** | Basic | Complete audit trail |
| **Inventory** | Simple deduction | Reservation system |
| **Error Handling** | None | Full logging |
| **Metrics** | None | Comprehensive tracking |
| **Notifications** | Immediate | Queued with retry |
| **Automation** | Manual | Fully automated |
| **Performance** | Moderate | Highly optimized |

---

## 🔧 Configuration

### **Enable Event Scheduler** (if not already enabled)

```sql
SET GLOBAL event_scheduler = ON;
```

**Add to `my.cnf` / `my.ini` for permanent:**
```ini
[mysqld]
event_scheduler = ON
```

### **Adjust Memory Settings** (optional, for high traffic)

```ini
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
max_connections = 500
```

---

## 📈 Usage Examples

### **Create an Order (with automatic inventory reservation)**

```sql
-- Insert order
INSERT INTO orders (
    order_number, user_id, subtotal, shipping_fee, 
    total_amount, payment_method, order_status
) VALUES (
    'ORD-20251017-12345', 1, 2000.00, 100.00, 
    2100.00, 'cod', 'pending'
);

SET @order_id = LAST_INSERT_ID();

-- Insert order items
INSERT INTO order_items (
    order_id, product_id, product_name, sku,
    quantity, unit_price, total_price
) VALUES (
    @order_id, 1, 'Samsung Galaxy S24', 'SAMS24-256',
    1, 2000.00, 2000.00
);

-- Reserve inventory (automatic locking)
CALL sp_reserve_order_inventory(@order_id, 30);
-- ✅ Stock reserved for 30 minutes
-- ✅ Inventory automatically deducted
-- ✅ Reservation record created
```

### **Check Pending Orders**

```sql
SELECT * FROM vw_pending_orders
WHERE action_required = 'Awaiting Confirmation'
ORDER BY minutes_pending DESC;
```

### **Check Inventory Status**

```sql
SELECT * FROM vw_inventory_status
WHERE stock_status IN ('LOW_STOCK', 'OUT_OF_STOCK');
```

### **Confirm Order (commits inventory)**

```sql
UPDATE orders 
SET order_status = 'confirmed', confirmed_at = NOW()
WHERE id = @order_id;

-- Commit inventory reservation
CALL sp_commit_order_inventory(@order_id);

-- ✅ State history automatically recorded (trigger)
-- ✅ Reservation marked as committed
-- ✅ Ready for fulfillment
```

### **Cancel Order (releases inventory)**

```sql
UPDATE orders 
SET order_status = 'cancelled', 
    cancelled_at = NOW(),
    cancellation_reason = 'Customer request'
WHERE id = @order_id;

-- Release inventory
CALL sp_release_order_inventory(@order_id, 'Order cancelled');

-- ✅ Stock automatically restored
-- ✅ Reservation released
-- ✅ State history recorded
```

### **Get Complete Order Details**

```sql
CALL sp_get_order_details(@order_id);

-- Returns:
-- 1. Order with customer info
-- 2. All order items
-- 3. Verification details (if any)
-- 4. Last 10 state changes
```

---

## 📊 Monitoring Queries

### **Today's Performance**

```sql
SELECT * FROM vw_daily_metrics
WHERE date = CURDATE();
```

### **Orders Requiring Attention**

```sql
SELECT 
    order_number,
    facebook_name as customer,
    total_amount,
    action_required,
    minutes_pending
FROM vw_pending_orders
WHERE minutes_pending > 60
ORDER BY minutes_pending DESC;
```

### **Low Stock Alerts**

```sql
SELECT 
    name,
    current_stock,
    reserved_quantity,
    available_stock,
    low_stock_threshold
FROM vw_inventory_status
WHERE stock_status = 'LOW_STOCK'
ORDER BY available_stock ASC;
```

### **Customer Lifetime Value**

```sql
SELECT 
    facebook_name,
    customer_tier,
    total_orders,
    total_spent,
    days_since_last_order,
    customer_status
FROM vw_customer_ltv
WHERE customer_status = 'ACTIVE'
ORDER BY total_spent DESC
LIMIT 20;
```

### **Processing Performance**

```sql
SELECT 
    AVG(total_processing_duration_ms) as avg_ms,
    MAX(total_processing_duration_ms) as max_ms,
    MIN(total_processing_duration_ms) as min_ms,
    COUNT(*) as total_orders
FROM order_metrics
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR);
```

### **Error Summary**

```sql
SELECT 
    error_type,
    severity,
    COUNT(*) as error_count,
    COUNT(CASE WHEN is_resolved = FALSE THEN 1 END) as unresolved
FROM order_errors
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY error_type, severity
ORDER BY error_count DESC;
```

---

## 🔐 Security Setup

### **Create Admin User**

```sql
INSERT INTO admin_users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@quicksell.com',
    -- Use bcrypt in your application
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eoT9qbE3NJke', 
    'System Administrator',
    'super_admin'
);
```

### **Grant Permissions (create app user)**

```sql
CREATE USER 'quicksell_app'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON quicksell_chatbot.* TO 'quicksell_app'@'localhost';
GRANT EXECUTE ON PROCEDURE quicksell_chatbot.* TO 'quicksell_app'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🧹 Maintenance

### **Manual Cleanup (if needed)**

```sql
-- Release stuck reservations
CALL sp_release_order_inventory(
    (SELECT order_id FROM inventory_reservations 
     WHERE status = 'reserved' AND expires_at < NOW() LIMIT 1),
    'Manual cleanup'
);

-- Remove old logs
DELETE FROM chat_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Optimize tables
OPTIMIZE TABLE orders, order_items, products;
```

### **Backup**

```bash
# Full backup
mysqldump -u root -p quicksell_chatbot > quicksell_backup_$(date +%Y%m%d).sql

# Backup with compression
mysqldump -u root -p quicksell_chatbot | gzip > quicksell_backup_$(date +%Y%m%d).sql.gz
```

### **Restore**

```bash
mysql -u root -p quicksell_chatbot < quicksell_backup_20251017.sql
```

---

## ✅ Post-Installation Checklist

- [ ] Database created successfully
- [ ] All 27 tables present
- [ ] 3 triggers active
- [ ] 4 procedures created
- [ ] 5 views working
- [ ] 3 events scheduled
- [ ] Event scheduler enabled
- [ ] Permissions configured
- [ ] Backup script created
- [ ] Application connection tested
- [ ] Sample order created
- [ ] Inventory reservation tested
- [ ] Views returning data
- [ ] Triggers firing correctly

---

## 🆘 Troubleshooting

### **Event Scheduler Not Running**

```sql
SET GLOBAL event_scheduler = ON;
SHOW VARIABLES LIKE 'event_scheduler';
```

### **Trigger Not Firing**

```sql
SHOW TRIGGERS;
SELECT * FROM order_state_history; -- Check if records are created
```

### **Procedure Error**

```sql
SHOW PROCEDURE STATUS WHERE Db = 'quicksell_chatbot';
CALL sp_reserve_order_inventory(1, 30); -- Test with real order
```

### **View Empty**

```sql
-- Check if base tables have data
SELECT COUNT(*) FROM orders;
SELECT * FROM vw_orders_detailed LIMIT 5;
```

---

## 📚 Next Steps

1. ✅ Database installed
2. Update your application to use new services:
   - `services/order_processor.py`
   - `services/order_validator.py`
3. Test order creation with enterprise features
4. Monitor metrics and performance
5. Set up regular backups

---

**Database Version:** 2.0.0  
**Installation Time:** ~10 minutes  
**Status:** ✅ Production Ready  
**Features:** Enterprise Grade  

**Your database is now world-class!** 🎉
