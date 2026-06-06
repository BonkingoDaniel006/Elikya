from flask import Flask
from config import Config
from ext import bcrypt, login_manager, mail, csrf
from auth.routes import auth_bp
from auth.models import User
from profils.routes import buyer_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation des extensions avec l'application Flask
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Enregistrement du Blueprint d'authentification
    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    """Fonction obligatoire pour Flask-Login permettant de recharger l'utilisateur depuis la session."""
    return User.get_by_id(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)