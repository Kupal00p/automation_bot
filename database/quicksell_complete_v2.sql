-- ================================================
-- QUICKSELL V2.0 - COMPLETE DATABASE SCHEMA
-- Enterprise-Grade E-Commerce Database
-- Production Ready | Scalable | Secure
-- ================================================

DROP DATABASE IF EXISTS quicksell_chatbot;
CREATE DATABASE quicksell_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quicksell_chatbot;

SET FOREIGN_KEY_CHECKS=0;

-- ================================================
-- PART 1: CORE TABLES
-- ================================================

-- Categories
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    parent_id INT NULL,
    description TEXT,
    icon_emoji VARCHAR(10),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_parent (parent_id),
    INDEX idx_slug (slug),
    INDEX idx_active_order (is_active, display_order)
) ENGINE=InnoDB;

-- Brands
CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    logo_url VARCHAR(500),
    description TEXT,
    website VARCHAR(255),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_featured (is_featured)
) ENGINE=InnoDB;

-- Users (Customers)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    messenger_id VARCHAR(100) UNIQUE NOT NULL,
    facebook_name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    customer_tier ENUM('regular', 'silver', 'gold', 'platinum') DEFAULT 'regular',
    loyalty_points INT DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0.00,
    total_orders INT DEFAULT 0,
    account_status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_messenger (messenger_id),
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_tier (customer_tier),
    INDEX idx_status (account_status),
    INDEX idx_tier_status (customer_tier, account_status),
    INDEX idx_total_spent (total_spent)
) ENGINE=InnoDB;

-- Admin Users
CREATE TABLE admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM('super_admin', 'admin', 'manager', 'staff') DEFAULT 'staff',
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB;

-- Products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    brand_id INT NOT NULL,
    description TEXT,
    specifications JSON,
    base_price DECIMAL(10, 2) NOT NULL,
    cost_price DECIMAL(10, 2),
    stock_quantity INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 5,
    weight_kg DECIMAL(8, 3),
    dimensions_cm VARCHAR(50),
    status ENUM('active', 'inactive', 'discontinued', 'coming_soon') DEFAULT 'active',
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    sales_count INT DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0.00,
    review_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT,
    INDEX idx_sku (sku),
    INDEX idx_slug (slug),
    INDEX idx_category (category_id),
    INDEX idx_brand (brand_id),
    INDEX idx_status (status),
    INDEX idx_featured (is_featured),
    INDEX idx_stock (stock_quantity),
    INDEX idx_price (base_price),
    INDEX idx_category_brand (category_id, brand_id),
    INDEX idx_status_stock (status, stock_quantity),
    INDEX idx_featured_status (is_featured, status),
    INDEX idx_sales_rating (sales_count, average_rating),
    FULLTEXT idx_search (name, description)
) ENGINE=InnoDB;

-- Product Images
CREATE TABLE product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    image_type ENUM('main', 'gallery', 'thumbnail') DEFAULT 'gallery',
    alt_text VARCHAR(255),
    display_order INT DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_primary (product_id, is_primary),
    INDEX idx_order (product_id, display_order)
) ENGINE=InnoDB;

-- Product Variants
CREATE TABLE product_variants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    variant_name VARCHAR(100) NOT NULL,
    variant_value VARCHAR(100) NOT NULL,
    sku_suffix VARCHAR(20),
    price_adjustment DECIMAL(10, 2) DEFAULT 0.00,
    stock_quantity INT DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_available (is_available),
    UNIQUE KEY unique_variant (product_id, variant_name, variant_value)
) ENGINE=InnoDB;

-- User Addresses
CREATE TABLE user_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_label VARCHAR(50),
    recipient_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    barangay VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10),
    region VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_default (user_id, is_default)
) ENGINE=InnoDB;

-- Promos
CREATE TABLE promos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    promo_code VARCHAR(50) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    promo_type ENUM('percentage', 'fixed_amount', 'free_shipping', 'bundle') DEFAULT 'percentage',
    discount_value DECIMAL(10, 2),
    min_purchase_amount DECIMAL(10, 2),
    max_discount_amount DECIMAL(10, 2),
    usage_limit INT,
    usage_count INT DEFAULT 0,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (promo_code),
    INDEX idx_active_dates (is_active, start_date, end_date)
) ENGINE=InnoDB;

-- Promo Products
CREATE TABLE promo_products (
    promo_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (promo_id, product_id),
    FOREIGN KEY (promo_id) REFERENCES promos(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ================================================
-- PART 2: ORDER TABLES (ENTERPRISE ENHANCED)
-- ================================================

-- Orders
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    address_id INT,
    
    -- Amounts
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    shipping_fee DECIMAL(10, 2) DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    upfront_paid DECIMAL(10, 2) DEFAULT 0.00,
    remaining_balance DECIMAL(10, 2),
    
    -- Payment
    promo_code VARCHAR(50),
    payment_method ENUM('cod', 'gcash', 'bank_transfer', 'credit_card', 'paymaya') DEFAULT 'cod',
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    
    -- Status
    order_status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    
    -- Verification
    verification_required BOOLEAN DEFAULT FALSE,
    verification_status ENUM('not_required', 'pending', 'under_review', 'verified', 'rejected') DEFAULT 'not_required',
    verification_type VARCHAR(50),
    verification_expires_at TIMESTAMP NULL,
    
    -- Metadata
    notes TEXT,
    tracking_number VARCHAR(100),
    cancellation_reason TEXT,
    
    -- Order Processing
    locked_at TIMESTAMP NULL,
    locked_by VARCHAR(100) NULL,
    lock_reason VARCHAR(255) NULL,
    processing_started_at TIMESTAMP NULL,
    processing_completed_at TIMESTAMP NULL,
    
    -- Error Tracking
    error_count INT DEFAULT 0,
    last_error TEXT NULL,
    retry_count INT DEFAULT 0,
    
    -- Source Tracking
    order_source ENUM('messenger', 'web', 'mobile_app', 'admin', 'api') DEFAULT 'messenger',
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    
    -- Timestamps
    confirmed_at TIMESTAMP NULL,
    shipped_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (address_id) REFERENCES user_addresses(id) ON DELETE SET NULL,
    
    INDEX idx_order_number (order_number),
    INDEX idx_user (user_id),
    INDEX idx_status (order_status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created (created_at),
    INDEX idx_verification_status (verification_status),
    INDEX idx_verification_expires (verification_expires_at),
    INDEX idx_user_status (user_id, order_status),
    INDEX idx_payment_combo (payment_status, payment_method),
    INDEX idx_verification_combo (verification_required, verification_status),
    INDEX idx_locked (locked_at, locked_by),
    INDEX idx_processing (processing_started_at, processing_completed_at),
    INDEX idx_created_status (created_at, order_status)
) ENGINE=InnoDB;

-- Order Items
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT,
    product_name VARCHAR(255) NOT NULL,
    variant_details VARCHAR(255),
    sku VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    
    -- Inventory Tracking
    inventory_reserved BOOLEAN DEFAULT FALSE,
    inventory_reserved_at TIMESTAMP NULL,
    inventory_released_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE SET NULL,
    
    INDEX idx_order (order_id),
    INDEX idx_product (product_id),
    INDEX idx_product_variant (product_id, variant_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Order State History
CREATE TABLE order_state_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by VARCHAR(100),
    changed_by_type ENUM('system', 'admin', 'customer', 'automation') DEFAULT 'system',
    reason TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    INDEX idx_order (order_id),
    INDEX idx_status (to_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Order Processing Queue
CREATE TABLE order_processing_queue (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    queue_type ENUM('new_order', 'payment', 'fulfillment', 'notification', 'verification') NOT NULL,
    priority TINYINT DEFAULT 5 COMMENT '1=highest, 10=lowest',
    status ENUM('pending', 'processing', 'completed', 'failed', 'retry') DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    payload JSON,
    result JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    INDEX idx_order (order_id),
    INDEX idx_status_priority (status, priority),
    INDEX idx_scheduled (scheduled_at),
    INDEX idx_queue_type (queue_type)
) ENGINE=InnoDB;

-- Inventory Reservations
CREATE TABLE inventory_reservations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    order_item_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT NULL,
    quantity INT NOT NULL,
    status ENUM('reserved', 'committed', 'released', 'expired') DEFAULT 'reserved',
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    committed_at TIMESTAMP NULL,
    released_at TIMESTAMP NULL,
    release_reason VARCHAR(255),
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (order_item_id) REFERENCES order_items(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE SET NULL,
    
    INDEX idx_order (order_id),
    INDEX idx_product (product_id),
    INDEX idx_status (status),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- Order Errors
CREATE TABLE order_errors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    error_type ENUM('validation', 'payment', 'inventory', 'shipping', 'system', 'external_api') NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    error_details JSON,
    stack_trace TEXT,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    INDEX idx_order (order_id),
    INDEX idx_type (error_type),
    INDEX idx_severity (severity),
    INDEX idx_resolved (is_resolved),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Order Metrics
CREATE TABLE order_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    validation_duration_ms INT,
    payment_duration_ms INT,
    fulfillment_duration_ms INT,
    total_processing_duration_ms INT,
    queue_wait_time_ms INT,
    customer_response_time_ms INT,
    error_count INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ================================================
-- PART 3: VERIFICATION TABLES
-- ================================================

-- Order Verifications
CREATE TABLE order_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    verification_type ENUM('id_verification', 'upfront_payment') NOT NULL,
    verification_status ENUM('pending', 'under_review', 'approved', 'rejected') DEFAULT 'pending',
    
    -- ID Verification
    id_image_url VARCHAR(500),
    selfie_image_url VARCHAR(500),
    id_type VARCHAR(50),
    id_notes TEXT,
    
    -- Payment Verification
    upfront_amount DECIMAL(10, 2),
    payment_proof_url VARCHAR(500),
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    
    -- Review
    reviewed_by INT,
    reviewed_at TIMESTAMP NULL,
    rejection_reason TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES admin_users(id) ON DELETE SET NULL,
    
    INDEX idx_order (order_id),
    INDEX idx_user (user_id),
    INDEX idx_status (verification_status),
    INDEX idx_type (verification_type),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- User Verification History
CREATE TABLE user_verification_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    verification_count INT DEFAULT 0,
    successful_verifications INT DEFAULT 0,
    failed_verifications INT DEFAULT 0,
    trust_score DECIMAL(3, 2) DEFAULT 0.00,
    is_verified_buyer BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_user (user_id),
    INDEX idx_trust_score (trust_score),
    INDEX idx_verified (is_verified_buyer)
) ENGINE=InnoDB;

-- Trusted Buyers
CREATE TABLE trusted_buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    trust_level ENUM('bronze', 'silver', 'gold', 'platinum') DEFAULT 'bronze',
    successful_orders INT DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0.00,
    verification_skip_enabled BOOLEAN DEFAULT FALSE,
    notes TEXT,
    granted_by INT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES admin_users(id) ON DELETE SET NULL,
    
    UNIQUE KEY unique_user (user_id),
    INDEX idx_trust_level (trust_level),
    INDEX idx_skip_enabled (verification_skip_enabled)
) ENGINE=InnoDB;

-- ================================================
-- PART 4: SUPPORTING TABLES
-- ================================================

-- Cart Items
CREATE TABLE cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT,
    quantity INT DEFAULT 1 CHECK (quantity > 0),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_cart_item (user_id, product_id, variant_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- Wishlists
CREATE TABLE wishlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_wishlist (user_id, product_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- Product Reviews
CREATE TABLE product_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    order_id INT,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_title VARCHAR(255),
    review_text TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    helpful_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    
    INDEX idx_product (product_id),
    INDEX idx_user (user_id),
    INDEX idx_approved (is_approved),
    INDEX idx_rating (product_id, rating)
) ENGINE=InnoDB;

-- Notification Queue
CREATE TABLE notification_queue (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NULL,
    user_id INT NOT NULL,
    notification_type ENUM('order_confirmed', 'order_shipped', 'order_delivered', 'order_cancelled', 
                          'verification_required', 'verification_approved', 'verification_rejected',
                          'payment_received', 'low_stock', 'custom') NOT NULL,
    channel ENUM('messenger', 'email', 'sms', 'push') NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    template_name VARCHAR(100),
    template_data JSON,
    status ENUM('pending', 'sent', 'failed', 'bounced') DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_order (order_id),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_at),
    INDEX idx_type_channel (notification_type, channel)
) ENGINE=InnoDB;

-- Inventory Logs
CREATE TABLE inventory_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    variant_id INT,
    transaction_type ENUM('stock_in', 'stock_out', 'adjustment', 'return') NOT NULL,
    quantity_change INT NOT NULL,
    previous_stock INT NOT NULL,
    new_stock INT NOT NULL,
    reference_type ENUM('order', 'purchase', 'adjustment', 'return'),
    reference_id INT,
    notes TEXT,
    performed_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE,
    
    INDEX idx_product (product_id),
    INDEX idx_type (transaction_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Chatbot Replies
CREATE TABLE chatbot_replies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    response TEXT NOT NULL,
    category VARCHAR(50),
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_keyword (keyword),
    INDEX idx_active (is_active),
    INDEX idx_priority (priority),
    FULLTEXT idx_search (keyword, response)
) ENGINE=InnoDB;

-- Chat Logs
CREATE TABLE chat_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    message_type ENUM('text', 'postback', 'quick_reply') DEFAULT 'text',
    user_message TEXT,
    bot_response TEXT,
    intent VARCHAR(100),
    payload VARCHAR(255),
    response_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id),
    INDEX idx_session (session_id),
    INDEX idx_created (created_at),
    INDEX idx_intent (intent)
) ENGINE=InnoDB;

-- Shipping Zones
CREATE TABLE shipping_zones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    zone_type ENUM('metro', 'provincial', 'island', 'international') DEFAULT 'provincial',
    base_fee DECIMAL(10, 2) NOT NULL,
    per_kg_fee DECIMAL(10, 2) DEFAULT 0.00,
    free_shipping_threshold DECIMAL(10, 2) DEFAULT 5000.00,
    estimated_days VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_type (zone_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Analytics Daily
CREATE TABLE analytics_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_sales DECIMAL(12, 2) DEFAULT 0.00,
    total_orders INT DEFAULT 0,
    new_customers INT DEFAULT 0,
    avg_order_value DECIMAL(10, 2) DEFAULT 0.00,
    top_product_id INT,
    top_category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_date (date)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS=1;

SELECT '✅ QuickSell V2.0 Database Created Successfully!' AS Status;
SELECT COUNT(*) AS TotalTables FROM information_schema.tables WHERE table_schema = 'quicksell_chatbot';
