from flask import Flask
import mysql.connector
from config import Config
from ext import bcrypt, login_manager
from auth.routes import auth_bp
from auth.models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation des extensions avec l'application Flask
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Enregistrement du Blueprint d'authentification
    app.register_blueprint(auth_bp)

    # Création automatique de la table "users" si elle n'existe pas
    init_db()

    return app

@login_manager.user_loader
def load_user(user_id):
    """Fonction obligatoire pour Flask-Login permettant de recharger l'utilisateur depuis la session."""
    return User.get_by_id(int(user_id))

def init_db():
    """Crée la table 'users' de manière sécurisée si elle n'existe pas."""
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor()
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)