from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import mysql.connector.pooling
# from config import Config # Ne pas importer Config directement au niveau du module

# Initialisation du pool de connexions (une seule fois pour toute l'app)
db_pool = None # Initialiser db_pool à None

def init_db_pool(app_config_dict):
    """Initialise le pool de connexions à la base de données."""
    global db_pool
    if db_pool is None: # S'assurer qu'il n'est initialisé qu'une seule fois
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="elikya_pool",
            pool_size=1,
            host=app_config_dict['MYSQL_HOST'],
            user=app_config_dict['MYSQL_USER'],
            password=app_config_dict['MYSQL_PASSWORD'],
            database=app_config_dict['MYSQL_DB']
        )

def get_db_connection():
    """Fonction unique pour récupérer une connexion du pool"""
    return db_pool.get_connection()

# Initialisation à vide des extensions (pattern factory)
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Redirection automatique si un utilisateur non connecté tente d'accéder à une page protégée
login_manager.login_view = 'auth.connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"