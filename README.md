# QuickSell Facebook Messenger Bot

A modular Facebook Messenger chatbot for QuickSell e-commerce platform built with Flask and MySQL.

## 🏗️ Project Structure

```
automation_bot/
├── app.py                      # Main Flask application entry point
├── config.py                   # Configuration and settings
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── Dockerfile                 # Docker configuration
│
├── services/                  # Service layer (business logic)
│   ├── __init__.py
│   ├── db_service.py         # Database operations and connection pooling
│   ├── messenger_service.py  # Facebook Messenger API communications
│   ├── handlers_service.py   # Message and postback handlers
│   ├── product_service.py    # Product-related operations
│   └── order_service.py      # Order handling operations
│
└── utils/                     # Utility functions
    ├── __init__.py
    └── helpers.py            # General helper functions
```

## 📁 File Descriptions

### Root Files

#### `app.py`
- **Purpose**: Main application entry point
- **Responsibilities**:
  - Flask application initialization
  - Webhook endpoint (GET/POST)
  - Health check endpoint
  - First-time user tracking
  - Request routing

#### `config.py`
- **Purpose**: Centralized configuration
- **Contains**:
  - Logging setup
  - Facebook Messenger credentials
  - Database configuration
  - NLP model loading
  - Bot constants (pagination, limits, etc.)

### Services Layer

#### `services/db_service.py`
- **Purpose**: Database operations
- **Functions**:
  - `get_db_connection()` - Get connection from pool
  - `get_or_create_user()` - User management
  - `log_chat()` - Chat interaction logging
  - `get_keyword_reply()` - Predefined keyword responses

#### `services/messenger_service.py`
- **Purpose**: Facebook Messenger API wrapper
- **Functions**:
  - `send_message()` - Send text messages
  - `send_image()` - Send image attachments
  - `send_button_template()` - Send button templates
  - `send_typing_indicator()` - Show typing indicator
  - `mark_seen()` - Mark messages as seen

#### `services/handlers_service.py`
- **Purpose**: Handle user interactions
- **Functions**:
  - `handle_user_message()` - Process text messages
  - `handle_postback()` - Process button clicks
  - `send_auto_greeting()` - Welcome new users
  - `send_main_menu()` - Display main menu

#### `services/product_service.py`
- **Purpose**: Product catalog management
- **Functions**:
  - `get_categories()` - Fetch product categories
  - `show_categories()` - Display categories to user
  - `show_products_page()` - Display products with pagination
  - `show_product_details()` - Show detailed product info
  - `show_promos()` - Display active promotions
  - `show_shipping_info()` - Display shipping information

#### `services/order_service.py`
- **Purpose**: Order processing
- **Functions**:
  - `handle_order_request()` - Process order inquiries
  - `create_order()` - Create order in database (future)

### Utilities

#### `utils/helpers.py`
- **Purpose**: General utility functions
- **Functions**:
  - `truncate_text()` - Text truncation
  - `format_currency()` - Currency formatting
  - `validate_email()` - Email validation
  - `validate_phone()` - Phone number validation
  - `format_timestamp()` - DateTime formatting
  - `clean_text()` - Text sanitization
  - `generate_button_title()` - Button title generation

## 🔄 Bot Workflow

### 1. **Webhook Verification** (GET /webhook)
```
Facebook → GET /webhook → Verify token → Return challenge
```

### 2. **Message Reception** (POST /webhook)
```
Facebook → POST /webhook → Parse event → Route to handler
```

### 3. **User Message Flow**
```
User sends message
    ↓
get_or_create_user()
    ↓
First-time user? → send_auto_greeting()
    ↓
handle_user_message()
    ↓
├─ Check keyword replies (DB)
├─ Check greetings
├─ Check "menu" command
└─ Use NLP model / Fallback
    ↓
send_message() / send_button_template()
    ↓
log_chat()
```

### 4. **Postback Flow** (Button Clicks)
```
User clicks button
    ↓
handle_postback(payload)
    ↓
├─ MAIN_MENU → send_main_menu()
├─ VIEW_PRODUCTS → show_categories()
├─ SHIPPING_INFO → show_shipping_info()
├─ VIEW_PROMOS → show_promos()
├─ CATEGORY_{slug} → show_products_page()
├─ PRODUCT_{id} → show_product_details()
├─ ORDER_{id} → handle_order_request()
└─ SHOW_MORE/SHOW_PREVIOUS → Pagination
```

### 5. **Product Browsing Flow**
```
Main Menu
    ↓
View Products → Categories (paginated)
    ↓
Select Category → Products List (paginated)
    ↓
Select Product → Product Details + Images
    ↓
Order Now → Order Request Handler
```

## 🗄️ Database Schema (Referenced)

### Tables Used:
- `users` - User information
- `chat_logs` - Conversation history
- `chatbot_replies` - Predefined keyword responses
- `categories` - Product categories
- `products` - Product catalog
- `product_images` - Product photos
- `brands` - Product brands
- `promos` - Promotional offers
- `shipping_zones` - Shipping fee information

## ⚙️ Environment Variables

Required environment variables (see `.env.example`):

```env
# Facebook Messenger
VERIFY_TOKEN=your_verify_token
PAGE_ACCESS_TOKEN=your_page_access_token

# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=quicksell_db

# Application
PORT=5000
DEBUG=False
```

## 🚀 Running the Bot

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Expose with ngrok** (for webhook testing):
   ```bash
   ngrok http 5000
   ```

### Docker Deployment

```bash
docker build -t quicksell-bot .
docker run -p 5000:5000 --env-file .env quicksell-bot
```

## 🧪 Testing Endpoints

### Health Check
```bash
GET http://localhost:5000/health
```

### Root
```bash
GET http://localhost:5000/
```

### Webhook
```bash
GET http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=CHALLENGE
```

## 📝 Key Features

- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Database Connection Pooling** - Efficient DB operations
- ✅ **NLP Integration** - Intent detection for natural conversations
- ✅ **Product Catalog** - Browse categories and products
- ✅ **Pagination** - Navigate large product lists
- ✅ **Image Support** - Display product photos
- ✅ **Order Management** - Handle order inquiries
- ✅ **Promo Support** - Display promotional offers
- ✅ **Shipping Info** - Zone-based shipping fees
- ✅ **Chat Logging** - Track all interactions
- ✅ **First-time Greeting** - Welcome new users
- ✅ **Error Handling** - Graceful error recovery

## 🔧 Extending the Bot

### Adding a New Feature

1. **Add service function** in appropriate service file
2. **Add handler** in `handlers_service.py`
3. **Add payload** handling in `handle_postback()`
4. **Update menu** if needed in `send_main_menu()`

### Example: Adding a "Track Order" Feature

1. Create `services/tracking_service.py`:
   ```python
   def show_order_status(sender_id, order_id):
       # Implementation
   ```

2. Update `handlers_service.py`:
   ```python
   elif payload.startswith("TRACK_"):
       order_id = payload.split("_")[1]
       show_order_status(sender_id, order_id)
   ```

3. Add button to menu:
   ```python
   {"type": "postback", "title": "📦 Track Order", "payload": "TRACK_MENU"}
   ```

## 📊 Workflow Diagram

```
┌─────────────────┐
│  Facebook User  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   app.py        │ ◄── Main entry point
│   /webhook      │
└────────┬────────┘
         │
         ├─► GET  → Verification
         │
         └─► POST → Message Processing
                    │
                    ▼
         ┌──────────────────────┐
         │ handlers_service.py  │
         │ ├─ handle_user_msg   │
         │ └─ handle_postback   │
         └──────────┬───────────┘
                    │
         ┌──────────┴───────────┐
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ product_service  │   │  order_service   │
│ - Categories     │   │  - Order Request │
│ - Products       │   │  - Create Order  │
│ - Promos         │   └──────────────────┘
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ messenger_service│
│ - send_message   │
│ - send_image     │
│ - send_template  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  db_service      │
│ - log_chat       │
│ - get_user       │
└──────────────────┘
```

## 📚 Additional Resources

- [Facebook Messenger Platform Documentation](https://developers.facebook.com/docs/messenger-platform)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)

## 📄 License

This project is part of the QuickSell e-commerce platform.

---

**Version**: 1.0.0  
**Last Updated**: 2025
