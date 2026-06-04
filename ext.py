from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialisation à vide des extensions (pattern factory)
bcrypt = Bcrypt()
login_manager = LoginManager()

# Redirection automatique si un utilisateur non connecté tente d'accéder à une page protégée
login_manager.login_view = 'auth.connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"