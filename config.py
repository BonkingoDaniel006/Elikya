import os 
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30) # <-- AJOUT : Déconnexion après 30 minutes

    # --- Configuration de sécurité des Cookies (centralisée) ---
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() in ('true', '1', 't')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
 
    # --- Configuration Redis pour le rate limiting et les sessions ---
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    MYSQL_HOST = os.environ.get('DB_HOST')
    MYSQL_USER = os.environ.get('DB_USER')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD')
    MYSQL_DB = os.environ.get('DB_NAME')
    MYSQL_CURSORCLASS = 'DictCursor'

    # Configuration Flask-Mail (Logique de l'architecte)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.environ.get("PROV_EMAIL")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # --- Configuration Shwary (basée sur sdk.md) ---
    # 1. Identifiant du marchand
    SHWARY_MERCHANT_ID = os.getenv("SHWARY_MERCHANT_ID", "0e0ca537-1d67-414d-8f13-3238be68766e")

    # 2. Clé secrète du marchand
    SHWARY_MERCHANT_KEY = os.getenv("SHWARY_MERCHANT_KEY", "shwary_d68f0f5d-e7d9-4fb6-ab1d-36f480d0ec9f")

    # 3. URL de callback que Shwary appellera
    SHWARY_CALLBACK_URL = os.getenv("SHWARY_CALLBACK_URL", "https://essaie-shwary-1.onrender.com/api/webhooks/shwary")

    # 4. Mode Sandbox (désactivé comme dans votre exemple)
    SHWARY_SANDBOX = os.getenv("SHWARY_SANDBOX", "false").lower() in ("1", "true", "yes")
