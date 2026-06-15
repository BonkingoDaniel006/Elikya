import logging
from flask import Flask
from config import Config
from ext import bcrypt, login_manager, mail, csrf, init_db_pool # Importer init_db_pool
from ext import get_db_connection # S'assurer que get_db_connection est importé si utilisé ailleurs
from auth.routes import auth_bp
from auth.models import User
from profils.routes import buyer_bp, seller_bp
from feed.routes import feed_bp
from produits.routes import produit_bp
from panier.routes import panier_bp
from notifications.routes import notifications_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuration des logs pour capturer les erreurs en production
    logging.basicConfig(level=logging.INFO)

    # Vérification des variables critiques au démarrage
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        app.logger.error("❌ ERREUR CRITIQUE : PROV_EMAIL ou MAIL_PASSWORD non définis !")
    else:
        app.logger.info(f"✅ Configuration Mail prête pour : {app.config.get('MAIL_USERNAME')}")
        app.logger.info(f"🔹 SMTP Port: {app.config.get('MAIL_PORT')} | SSL: {app.config.get('MAIL_USE_SSL')} | TLS: {app.config.get('MAIL_USE_TLS')}")
    
        # Initialiser le pool de base de données APRÈS que la configuration de l'application soit chargée
    init_db_pool(app.config)
    # Initialisation des extensions avec l'application Flask
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Enregistrement du Blueprint d'authentification
    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(produit_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(panier_bp)
    app.register_blueprint(notifications_bp)


    return app

@login_manager.user_loader
def load_user(user_id):
    """Fonction obligatoire pour Flask-Login permettant de recharger l'utilisateur depuis la session."""
    return User.get_by_id(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)