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
    CSRF_MAX_AGE_SECONDS = 3600 # Durée de vie du token CSRF (1 heure)
 
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


    PAYMENT_MICROSERVICE_URL = os.getenv('PAYMENT_MICROSERVICE_URL')
