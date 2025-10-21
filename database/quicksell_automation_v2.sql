-- ================================================
-- QUICKSELL V2.0 - AUTOMATION LAYER
-- MySQL Workbench Compatible Version
-- Run this AFTER quicksell_complete_v2.sql
-- ================================================

USE quicksell_chatbot;

-- Drop existing objects if they exist
DROP TRIGGER IF EXISTS after_order_status_update;
DROP TRIGGER IF EXISTS after_order_delivered;
DROP TRIGGER IF EXISTS after_product_stock_change;
DROP PROCEDURE IF EXISTS sp_reserve_order_inventory;
DROP PROCEDURE IF EXISTS sp_release_order_inventory;
DROP PROCEDURE IF EXISTS sp_commit_order_inventory;
DROP PROCEDURE IF EXISTS sp_get_order_details;
DROP VIEW IF EXISTS vw_orders_detailed;
DROP VIEW IF EXISTS vw_pending_orders;
DROP VIEW IF EXISTS vw_inventory_status;
DROP VIEW IF EXISTS vw_daily_metrics;
DROP VIEW IF EXISTS vw_customer_ltv;
DROP EVENT IF EXISTS evt_cleanup_expired_reservations;
DROP EVENT IF EXISTS evt_cleanup_old_queue_items;
DROP EVENT IF EXISTS evt_update_daily_analytics;

-- ================================================
-- PART 1: TRIGGERS FOR AUTOMATION
-- ================================================

DELIMITER $$

CREATE TRIGGER after_order_status_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.order_status <> NEW.order_status THEN
        INSERT INTO order_state_history (
            order_id, 
            from_status, 
            to_status, 
            changed_by_type,
            reason
        ) VALUES (
            NEW.id,
            OLD.order_status,
            NEW.order_status,
            'system',
            CONCAT('Status changed from ', OLD.order_status, ' to ', NEW.order_status)
        );
    END IF;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE TRIGGER after_order_delivered
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF NEW.order_status = 'delivered' AND OLD.order_status <> 'delivered' THEN
        UPDATE users 
        SET 
            total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total_amount,
            customer_tier = CASE
                WHEN (total_spent + NEW.total_amount) >= 100000 THEN 'platinum'
                WHEN (total_spent + NEW.total_amount) >= 50000 THEN 'gold'
                WHEN (total_spent + NEW.total_amount) >= 20000 THEN 'silver'
                ELSE 'regular'
            END
        WHERE id = NEW.user_id;
    END IF;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE TRIGGER after_product_stock_change
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF OLD.stock_quantity <> NEW.stock_quantity THEN
        INSERT INTO inventory_logs (
            product_id,
            transaction_type,
            quantity_change,
            previous_stock,
            new_stock,
            reference_type,
            notes
        ) VALUES (
            NEW.id,
            IF(NEW.stock_quantity > OLD.stock_quantity, 'stock_in', 'stock_out'),
            NEW.stock_quantity - OLD.stock_quantity,
            OLD.stock_quantity,
            NEW.stock_quantity,
            'adjustment',
            'Automatic inventory tracking'
        );
    END IF;
END$$

DELIMITER ;

-- ================================================
-- PART 2: STORED PROCEDURES
-- ================================================

DELIMITER $$

CREATE PROCEDURE sp_reserve_order_inventory(
    IN p_order_id INT,
    IN p_expiry_minutes INT
)
BEGIN
    DECLARE v_done INT DEFAULT FALSE;
    DECLARE v_item_id INT;
    DECLARE v_product_id INT;
    DECLARE v_variant_id INT;
    DECLARE v_quantity INT;
    DECLARE v_available_stock INT;
    DECLARE v_error_msg VARCHAR(500);
    
    DECLARE cur CURSOR FOR 
        SELECT id, product_id, variant_id, quantity 
        FROM order_items 
        WHERE order_id = p_order_id;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    
    START TRANSACTION;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_item_id, v_product_id, v_variant_id, v_quantity;
        
        IF v_done THEN
            LEAVE read_loop;
        END IF;
        
        -- Check and lock stock
        IF v_variant_id IS NULL THEN
            SELECT stock_quantity INTO v_available_stock
            FROM products
            WHERE id = v_product_id
            FOR UPDATE;
        ELSE
            SELECT stock_quantity INTO v_available_stock
            FROM product_variants
            WHERE id = v_variant_id
            FOR UPDATE;
        END IF;
        
        -- Validate availability
        IF v_available_stock < v_quantity THEN
            SET v_error_msg = CONCAT('Insufficient stock for product ', v_product_id);
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_error_msg;
        END IF;
        
        -- Create reservation
        INSERT INTO inventory_reservations (
            order_id, order_item_id, product_id, variant_id,
            quantity, status, expires_at
        ) VALUES (
            p_order_id, v_item_id, v_product_id, v_variant_id,
            v_quantity, 'reserved',
            DATE_ADD(NOW(), INTERVAL p_expiry_minutes MINUTE)
        );
        
        -- Deduct stock
        IF v_variant_id IS NULL THEN
            UPDATE products 
            SET stock_quantity = stock_quantity - v_quantity
            WHERE id = v_product_id;
        ELSE
            UPDATE product_variants
            SET stock_quantity = stock_quantity - v_quantity
            WHERE id = v_variant_id;
        END IF;
        
        -- Mark item as reserved
        UPDATE order_items
        SET inventory_reserved = TRUE, inventory_reserved_at = NOW()
        WHERE id = v_item_id;
        
    END LOOP;
    
    CLOSE cur;
    COMMIT;
    
    SELECT 'SUCCESS' as status, 'Inventory reserved successfully' as message;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE PROCEDURE sp_release_order_inventory(
    IN p_order_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    -- Release stock back to products
    UPDATE products p
    INNER JOIN inventory_reservations ir ON p.id = ir.product_id
    SET p.stock_quantity = p.stock_quantity + ir.quantity
    WHERE ir.order_id = p_order_id 
        AND ir.status = 'reserved'
        AND ir.variant_id IS NULL;
    
    -- Release stock back to variants
    UPDATE product_variants pv
    INNER JOIN inventory_reservations ir ON pv.id = ir.variant_id
    SET pv.stock_quantity = pv.stock_quantity + ir.quantity
    WHERE ir.order_id = p_order_id 
        AND ir.status = 'reserved';
    
    -- Update reservations
    UPDATE inventory_reservations
    SET status = 'released',
        released_at = NOW(),
        release_reason = p_reason
    WHERE order_id = p_order_id AND status = 'reserved';
    
    -- Update order items
    UPDATE order_items
    SET inventory_reserved = FALSE, inventory_released_at = NOW()
    WHERE order_id = p_order_id AND inventory_reserved = TRUE;
    
    SELECT 'SUCCESS' as status, 'Inventory released successfully' as message;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE PROCEDURE sp_commit_order_inventory(
    IN p_order_id INT
)
BEGIN
    UPDATE inventory_reservations
    SET status = 'committed', committed_at = NOW()
    WHERE order_id = p_order_id AND status = 'reserved';
    
    SELECT 'SUCCESS' as status, 'Inventory committed successfully' as message;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE PROCEDURE sp_get_order_details(
    IN p_order_id INT
)
BEGIN
    -- Get order with user details
    SELECT 
        o.*,
        u.messenger_id,
        u.facebook_name,
        u.email,
        u.phone,
        u.customer_tier,
        u.total_orders as user_total_orders,
        u.total_spent as user_total_spent
    FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    WHERE o.id = p_order_id;
    
    -- Get order items
    SELECT * FROM order_items WHERE order_id = p_order_id;
    
    -- Get verification if exists
    SELECT * FROM order_verifications WHERE order_id = p_order_id;
    
    -- Get state history
    SELECT * FROM order_state_history 
    WHERE order_id = p_order_id 
    ORDER BY created_at DESC 
    LIMIT 10;
END$$

DELIMITER ;

-- ================================================
-- PART 3: VIEWS FOR REPORTING
-- ================================================

CREATE VIEW vw_orders_detailed AS
SELECT 
    o.*,
    u.facebook_name as customer_name,
    u.email as customer_email,
    u.phone as customer_phone,
    u.customer_tier,
    COUNT(oi.id) as item_count,
    GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') as product_names,
    (SELECT COUNT(*) FROM order_errors oe 
     WHERE oe.order_id = o.id AND oe.is_resolved = FALSE) as unresolved_errors,
    TIMESTAMPDIFF(HOUR, o.created_at, o.delivered_at) as fulfillment_hours,
    om.total_processing_duration_ms
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN order_metrics om ON o.id = om.order_id
GROUP BY o.id;

-- ================================================

CREATE VIEW vw_pending_orders AS
SELECT 
    o.id,
    o.order_number,
    o.user_id,
    u.facebook_name,
    u.phone,
    o.total_amount,
    o.order_status,
    o.verification_required,
    o.verification_status,
    o.payment_status,
    o.created_at,
    TIMESTAMPDIFF(MINUTE, o.created_at, NOW()) as minutes_pending,
    CASE 
        WHEN o.verification_required AND o.verification_status IN ('pending', 'under_review') 
            THEN 'Awaiting Verification'
        WHEN o.order_status = 'pending' THEN 'Awaiting Confirmation'
        WHEN o.payment_status = 'pending' THEN 'Awaiting Payment'
        ELSE 'Pending Processing'
    END as action_required
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE o.order_status IN ('pending', 'confirmed')
   OR (o.verification_required AND o.verification_status IN ('pending', 'under_review'))
ORDER BY o.created_at ASC;

-- ================================================

CREATE VIEW vw_inventory_status AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.stock_quantity as current_stock,
    p.low_stock_threshold,
    COALESCE(SUM(CASE WHEN ir.status = 'reserved' THEN ir.quantity ELSE 0 END), 0) as reserved_quantity,
    p.stock_quantity - COALESCE(SUM(CASE WHEN ir.status = 'reserved' THEN ir.quantity ELSE 0 END), 0) as available_stock,
    CASE 
        WHEN p.stock_quantity <= 0 THEN 'OUT_OF_STOCK'
        WHEN p.stock_quantity <= p.low_stock_threshold THEN 'LOW_STOCK'
        ELSE 'IN_STOCK'
    END as stock_status
FROM products p
LEFT JOIN inventory_reservations ir ON p.id = ir.product_id AND ir.status = 'reserved'
WHERE p.status = 'active'
GROUP BY p.id;

-- ================================================

CREATE VIEW vw_daily_metrics AS
SELECT 
    DATE(o.created_at) as date,
    COUNT(*) as total_orders,
    SUM(CASE WHEN o.order_status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
    SUM(CASE WHEN o.order_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    AVG(om.total_processing_duration_ms) as avg_processing_ms,
    SUM(o.error_count) as total_errors
FROM orders o
LEFT JOIN order_metrics om ON o.id = om.order_id
GROUP BY DATE(o.created_at)
ORDER BY date DESC;

-- ================================================

CREATE VIEW vw_customer_ltv AS
SELECT 
    u.id,
    u.facebook_name,
    u.email,
    u.phone,
    u.customer_tier,
    u.total_orders,
    u.total_spent,
    u.loyalty_points,
    COUNT(o.id) as verified_order_count,
    MAX(o.created_at) as last_order_date,
    DATEDIFF(NOW(), MAX(o.created_at)) as days_since_last_order,
    CASE 
        WHEN u.total_orders = 0 THEN 'INACTIVE'
        WHEN DATEDIFF(NOW(), MAX(o.created_at)) > 90 THEN 'AT_RISK'
        WHEN DATEDIFF(NOW(), MAX(o.created_at)) > 30 THEN 'DORMANT'
        ELSE 'ACTIVE'
    END as customer_status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.order_status <> 'cancelled'
GROUP BY u.id;

-- ================================================
-- PART 4: SCHEDULED EVENTS
-- ================================================

SET GLOBAL event_scheduler = ON;

-- ================================================

DELIMITER $$

CREATE EVENT evt_cleanup_expired_reservations
ON SCHEDULE EVERY 5 MINUTE
DO
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_done INT DEFAULT FALSE;
    
    DECLARE cur CURSOR FOR
        SELECT DISTINCT order_id 
        FROM inventory_reservations 
        WHERE status = 'reserved' AND expires_at < NOW()
        LIMIT 10;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    
    OPEN cur;
    
    cleanup_loop: LOOP
        FETCH cur INTO v_order_id;
        
        IF v_done THEN
            LEAVE cleanup_loop;
        END IF;
        
        CALL sp_release_order_inventory(v_order_id, 'Reservation expired');
        
    END LOOP;
    
    CLOSE cur;
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE EVENT evt_cleanup_old_queue_items
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    -- Remove old completed processing queue items
    DELETE FROM order_processing_queue
    WHERE status = 'completed' 
        AND completed_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    
    -- Remove old sent notifications
    DELETE FROM notification_queue
    WHERE status = 'sent'
        AND sent_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Archive old chat logs (optional)
    DELETE FROM chat_logs
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
END$$

DELIMITER ;

-- ================================================

DELIMITER $$

CREATE EVENT evt_update_daily_analytics
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY)
DO
BEGIN
    INSERT INTO analytics_daily (date, total_sales, total_orders, new_customers, avg_order_value)
    SELECT 
        CURDATE() - INTERVAL 1 DAY as date,
        COALESCE(SUM(total_amount), 0) as total_sales,
        COUNT(*) as total_orders,
        (SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURDATE() - INTERVAL 1 DAY) as new_customers,
        COALESCE(AVG(total_amount), 0) as avg_order_value
    FROM orders
    WHERE DATE(created_at) = CURDATE() - INTERVAL 1 DAY
        AND order_status <> 'cancelled'
    ON DUPLICATE KEY UPDATE
        total_sales = VALUES(total_sales),
        total_orders = VALUES(total_orders),
        new_customers = VALUES(new_customers),
        avg_order_value = VALUES(avg_order_value);
END$$

DELIMITER ;

-- ================================================
-- COMPLETION MESSAGE
-- ================================================

SELECT '✅ Automation Layer Installed Successfully!' AS Status;
SELECT '3 Triggers Created' AS Triggers;
SELECT '4 Stored Procedures Created' AS Procedures;
SELECT '5 Views Created' AS Views;
SELECT '3 Scheduled Events Created' AS Events;
SELECT 'QuickSell V2.0 is now fully operational!' AS Message;
