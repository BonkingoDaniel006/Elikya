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
    
    # 1. On récupère l'identifiant du marchand fourni par Shwary depuis le fichier .env
    SHWARY_MERCHANT_ID = os.getenv("SHWARY_MERCHANT_ID")
    
    # 2. On récupère la clé secrète fournie par Shwary
    SHWARY_MERCHANT_KEY = os.getenv("SHWARY_MERCHANT_KEY")
    
    # 3. L'URL de base de l'API (avec une valeur par défaut si elle n'est pas dans le .env)
    SHWARY_BASE_URL = os.getenv("SHWARY_BASE_URL", "https://api.shwary.com")
    
    # 4. On définit l'URL (Webhook) que Shwary devra appeler pour nous dire si le paiement a réussi ou échoué.
    # Si on est en local, ça ressemble à http://127.0.0.1:5000/api/callback
    SHWARY_CALLBACK_URL = os.getenv("SHWARY_CALLBACK_URL") or "http://127.0.0.1:5000/api/callback"
    
    # 5. Un mode "Bac à sable" (Sandbox) pour faire de faux paiements pendant le développement.
    SHWARY_SANDBOX = os.getenv("SHWARY_SANDBOX", "true").lower() in ("1", "true", "yes")
