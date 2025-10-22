import os
import logging
import pickle
import ssl

# ================================================
# LOGGING SETUP
# ================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================
# FACEBOOK MESSENGER CONFIGURATION
# ================================================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secret_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "EAASk3ZAn0F6EBPo6jpVVtjdC9wW7qDqZBShDZCbbh5tWOGf8MXdssgu9dftyOVGOZBlGuM9A0kmRN8lt1ByilPWcE90MZBJ5S0LKbZARTLcJdafztIOGtAjGmFWyxAqyTPIhU4aLNrl3aEUm5YTlORMOZApMb3noz6ZBAH5NZA49jfwy2pZBmDGIYV4h4aCTNsMMde4kN1MgZDZD")

# ================================================
# DATABASE CONFIGURATION (MySQL - Aiven Cloud)
# ================================================
# SSL configuration for Aiven MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "database": os.getenv("DB_NAME", "defaultdb"),
    "pool_name": "quicksell_pool",
    "pool_size": 5,
    # SSL configuration - use TLS without strict certificate verification
    "ssl_disabled": False,
    "ssl_verify_cert": False,  # Disable strict cert verification for Aiven
    "ssl_verify_identity": False,
    "tls_versions": ['TLSv1.2', 'TLSv1.3']
}

# ================================================
# NLP MODEL CONFIGURATION
# ================================================
try:
    with open("intent_model.pkl", "rb") as f:
        vectorizer, model = pickle.load(f)
    logger.info("✅ NLP model loaded successfully")
except FileNotFoundError:
    vectorizer, model = None, None
    logger.warning("⚠️ NLP model not found - using fallback responses")

# ================================================
# BOT CONFIGURATION
# ================================================
PRODUCTS_PER_PAGE = 3
MAX_BUTTONS_PER_MESSAGE = 3
MAX_MESSAGE_LENGTH = 640
MAX_IMAGES_PER_PRODUCT = 5
