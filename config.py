import os 
from dotenv import load_dotenv
import secrets

load_dotenv()


def _env_bool(name, default="false"):
    return os.getenv(name, default).lower() in ("1", "true", "yes")



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'une_cle_tres_secrete_et_longue_12345')
    
    # Sécurité des Sessions (Indispensable pour la production en HTTPS)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    MYSQL_HOST = os.environ.get('DB_HOST')
    MYSQL_USER = os.environ.get('DB_USER')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD')
    MYSQL_DB = os.environ.get('DB_NAME')
    MYSQL_CURSORCLASS = 'DictCursor'

    # Configuration Flask-Mail optimisée pour la production (Gmail Port 465 SSL)
   
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.environ.get("PROV_EMAIL")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("PROV_EMAIL")
    MAIL_SUPPRESS_SEND = False


    SHWARY_MERCHANT_ID = os.getenv("SHWARY_MERCHANT_ID")
    
    # 2. On récupère la clé secrète fournie par Shwary
    SHWARY_MERCHANT_KEY = os.getenv("SHWARY_MERCHANT_KEY")
    
    # 3. L'URL de base de l'API (avec une valeur par défaut si elle n'est pas dans le .env)
    SHWARY_BASE_URL = os.getenv("SHWARY_BASE_URL", "https://api.shwary.com")
    
    # 4. On définit l'URL (Webhook) que Shwary devra appeler pour nous dire si le paiement a réussi ou échoué.
    # Si on est en local, ça ressemble à http://127.0.0.1:5000/api/callback
    SHWARY_CALLBACK_URL = os.getenv("SHWARY_CALLBACK_URL") or "http://127.0.0.1:5000/api/callback"
    
    # 5. Un mode "Bac à sable" (Sandbox) pour faire de faux paiements pendant le développement.
    SHWARY_SANDBOX = _env_bool("SHWARY_SANDBOX", "true")
