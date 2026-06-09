from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import mysql.connector.pooling
from config import Config

# Initialisation du pool de connexions (une seule fois pour toute l'app)
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="elikya_pool",
    pool_size=1,
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
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