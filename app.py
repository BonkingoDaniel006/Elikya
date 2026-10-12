import logging
import json
import time
import uuid
from flask import Flask, jsonify, session, flash, redirect, url_for, request, g
from config import Config
from flask_login import current_user, logout_user
from datetime import datetime
from mysql.connector import Error as MySQLError
from redis.exceptions import RedisError
from werkzeug.exceptions import ServiceUnavailable
from werkzeug.middleware.proxy_fix import ProxyFix
from ext import (
    bcrypt, login_manager, mail, csrf, init_db_pool, init_redis_client,
    init_rate_limiter, db_session, get_redis_client,
)
from auth.routes import auth_bp
from auth.models import User
from profils.routes import buyer_bp, seller_bp
from feed.routes import feed_bp
from produits.routes import produit_bp
from panier.routes import panier_bp
from notifications.routes import notifications_bp


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.config.from_object(Config)
    
    # Configuration des logs pour capturer les erreurs en production
    logging.basicConfig(level=logging.INFO)

    @app.before_request
    def start_request_logging():
        g.request_id = uuid.uuid4().hex
        g.request_started_at = time.perf_counter()

    @app.before_request
    def check_session_inactivity():
        """
        Déconnecte l'utilisateur si sa dernière activité remonte à plus de
        PERMANENT_SESSION_LIFETIME (30 minutes).
        """
        # Ne pas exécuter cette logique pour les endpoints 'static'
        if request.endpoint and request.endpoint == 'static':
            return

        if current_user.is_authenticated:
            now = time.time()
            last_activity = session.get('last_activity_time')
            try:
                last_activity = float(last_activity) if last_activity is not None else None
            except (TypeError, ValueError):
                last_activity = None
            session_lifetime = app.config.get('PERMANENT_SESSION_LIFETIME')

            if last_activity is not None and session_lifetime:
                elapsed_time = now - last_activity
                if elapsed_time > session_lifetime.total_seconds():
                    logout_user()
                    session.clear()
                    flash("Votre session a expiré pour inactivité. Veuillez vous reconnecter.", "info")
                    return redirect(url_for('auth.connexion'))
            if last_activity is None or now - last_activity >= 60:
                session['last_activity_time'] = now

    @app.context_processor
    def inject_now():
        """Rend la fonction now() disponible dans tous les templates."""
        # Utiliser datetime.utcnow pour être indépendant du fuseau horaire du serveur
        return {'now': datetime.utcnow}

    # Vérification des variables critiques au démarrage
    
        # Initialiser le pool de base de données APRÈS que la configuration de l'application soit chargée
    init_db_pool(app.config)
    init_redis_client(app.config)
    # Initialisation des extensions avec l'application Flask
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    init_rate_limiter(app)

    # Enregistrement du Blueprint d'authentification
    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(produit_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(panier_bp) # Cette ligne est cruciale pour activer le webhook
    app.register_blueprint(notifications_bp)

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - g.request_started_at) * 1000
        response.headers['X-Request-ID'] = g.request_id
        record = {
            'level': 'WARNING' if duration_ms > 500 else 'INFO',
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration_ms, 2),
        }
        log = app.logger.warning if duration_ms > 500 else app.logger.info
        log(json.dumps(record, ensure_ascii=False, separators=(',', ':')))
        return response

    @app.route('/healthz', methods=['GET'])
    def healthz():
        checks = {'mysql': False, 'redis': False}
        try:
            with db_session() as (_, cursor):
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks['mysql'] = True
        except (MySQLError, ServiceUnavailable):
            app.logger.warning("Health check MySQL indisponible.")

        try:
            redis_client = get_redis_client()
            if redis_client is not None:
                redis_client.ping()
                checks['redis'] = True
        except RedisError:
            app.logger.warning("Health check Redis indisponible.")

        status_code = 200 if all(checks.values()) else 503
        return jsonify(status="ok" if status_code == 200 else "unavailable", checks=checks), status_code

    @app.errorhandler(429)
    def handle_too_many_requests(error):
        return jsonify(
            error="Trop de requêtes. Veuillez réessayer plus tard.",
            request_id=getattr(g, 'request_id', None),
        ), 429

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        request_id = getattr(g, 'request_id', None)
        app.logger.error("Erreur interne; request_id=%s", request_id)
        return jsonify(
            error="Une erreur interne est survenue.",
            request_id=request_id,
        ), 500

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        app.logger.warning(
            "Service temporairement indisponible; request_id=%s: %s",
            getattr(g, 'request_id', None),
            error,
        )
        return jsonify(
            error="Service temporairement indisponible",
            request_id=getattr(g, 'request_id', None),
        ), 503

    return app

@login_manager.user_loader
def load_user(user_id):
    """Fonction obligatoire pour Flask-Login permettant de recharger l'utilisateur depuis la session."""
    return User.get_cached_by_id(int(user_id))


if __name__ == '__main__':
    app = create_app()
    if not app.config['FLASK_DEBUG']:
        raise SystemExit("Lancez l'application en production avec Gunicorn.")
    app.run(debug=True)