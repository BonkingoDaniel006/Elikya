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
    REDIS_URL = os.getenv('REDIS_URL', f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    REDIS_SOCKET_TIMEOUT = float(os.getenv('REDIS_SOCKET_TIMEOUT', 1))
    REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 1))
    REDIS_HEALTH_CHECK_INTERVAL = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', 30))
    RATELIMIT_STORAGE_URI = os.getenv(
        'RATELIMIT_STORAGE_URI',
        REDIS_URL,
    )
    RATELIMIT_SOCKET_TIMEOUT = float(os.getenv('RATELIMIT_SOCKET_TIMEOUT', 0.1))

    MYSQL_HOST = os.environ.get('DB_HOST')
    MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
    MYSQL_USER = os.environ.get('DB_USER')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD')
    MYSQL_DB = os.environ.get('DB_NAME')
    GUNICORN_THREADS = int(os.getenv('GUNICORN_THREADS', 4))
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', GUNICORN_THREADS + 2))
    USER_CACHE_TTL = int(os.getenv('USER_CACHE_TTL', 60))
    MYSQL_CURSORCLASS = 'DictCursor'

    # Transport email configurable : Brevo conserve le comportement actuel par défaut.
    EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'brevo').lower()
    EMAIL_SENDER = os.getenv('EMAIL_SENDER') or os.getenv("PROV_EMAIL", "")
    EMAIL_TIMEOUT_CONNECT = float(os.getenv('EMAIL_TIMEOUT_CONNECT', 2))
    EMAIL_TIMEOUT_READ = float(os.getenv('EMAIL_TIMEOUT_READ', 5))
    RQ_EMAIL_JOB_TIMEOUT = int(os.getenv('RQ_EMAIL_JOB_TIMEOUT', 15))

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() in ('true', '1', 't')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get("PROV_EMAIL")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")


    PAYMENT_MICROSERVICE_URL = os.getenv('PAYMENT_MICROSERVICE_URL')
