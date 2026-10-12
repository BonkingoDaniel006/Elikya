import logging
from contextlib import contextmanager

from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import mysql.connector.pooling
from mysql.connector.errors import PoolError
import redis
from werkzeug.exceptions import ServiceUnavailable
# from config import Config # Ne pas importer Config directement au niveau du module

logger = logging.getLogger(__name__)

# Initialisation du client Redis
redis_client = None

# Initialisation du pool de connexions (une seule fois pour toute l'app)
db_pool = None # Initialiser db_pool à None

def init_db_pool(app_config_dict):
    """Initialise le pool de connexions à la base de données."""
    global db_pool
    if db_pool is None: # S'assurer qu'il n'est initialisé qu'une seule fois
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="elikya_pool",
            pool_size=app_config_dict.get('DB_POOL_SIZE', 6),
            host=app_config_dict['MYSQL_HOST'],
            port=app_config_dict.get('MYSQL_PORT', 3306),
            user=app_config_dict['MYSQL_USER'],
            password=app_config_dict['MYSQL_PASSWORD'],
            database=app_config_dict['MYSQL_DB']
        )

def init_redis_client(app_config_dict):
    """Initialise le client Redis."""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=app_config_dict['REDIS_HOST'],
            port=app_config_dict['REDIS_PORT'],
            db=app_config_dict['REDIS_DB'],
            decode_responses=True,
            socket_timeout=app_config_dict.get('REDIS_SOCKET_TIMEOUT', 1),
            socket_connect_timeout=app_config_dict.get('REDIS_SOCKET_CONNECT_TIMEOUT', 1),
            health_check_interval=app_config_dict.get('REDIS_HEALTH_CHECK_INTERVAL', 30),
            retry_on_timeout=True
        )

def get_db_connection():
    """Fonction unique pour récupérer une connexion du pool"""
    if db_pool is None:
        raise ServiceUnavailable("Le service de base de données est indisponible.")
    try:
        return db_pool.get_connection()
    except PoolError as exc:
        logger.warning("Pool MySQL saturé; la requête ne peut pas obtenir de connexion.")
        raise ServiceUnavailable(
            "Le service de base de données est temporairement saturé."
        ) from exc


@contextmanager
def db_session(dictionary=False):
    """Ferme systématiquement curseur et connexion rendue au pool."""
    conn = get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
    except Exception:
        try:
            conn.rollback()
        except Exception:
            logger.exception("Échec du rollback après une erreur DB.")
        raise
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()

def get_redis_client():
    return redis_client

# Initialisation à vide des extensions (pattern factory)
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Redirection automatique si un utilisateur non connecté tente d'accéder à une page protégée
login_manager.login_view = 'auth.connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"