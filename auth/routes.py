from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
import random
import time
from redis.exceptions import ConnectionError as RedisConnectionError
from ext import bcrypt
from ext import get_redis_client, get_db_connection
from auth.models import User # Gardez cette ligne
from produits.models import Produits # MODIFICATION: Importer depuis produits.models
from auth.services import process_registration, process_otp_validation

auth_bp = Blueprint('auth', __name__)

MAX_ATTEMPTS = 5
LOCKOUT_PERIOD_SECONDS = 900  # 15 minutes


@auth_bp.route('/')
def racine():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    return redirect(url_for('auth.connexion'))

@auth_bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
        
    if request.method == 'POST':
        if request.form['password'] != request.form['confirm_password']:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template('inscription_etape1.html')

        # Étape 1: Collecte des informations de base
        user_data = {
            'nom': request.form['last_name'],
            'prenom': request.form['first_name'],
            'email': request.form['email'],
            'password': request.form['password']
        }

        # Stocker temporairement dans la session et passer à l'étape 2
        session['registration_step1_data'] = user_data
        return redirect(url_for('auth.inscription_profil'))
            
    return render_template('inscription_etape1.html')

@auth_bp.route('/inscription/profil', methods=['GET', 'POST'])
def inscription_profil():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    # S'assurer que l'utilisateur a bien complété l'étape 1
    if 'registration_step1_data' not in session:
        flash("Veuillez commencer par la première étape de l'inscription.", "warning")
        return redirect(url_for('auth.inscription'))

    if request.method == 'POST':
        # Vérifier si la politique de confidentialité a été acceptée
        if 'privacy_policy' not in request.form:
            flash("Vous devez accepter la politique de confidentialité pour continuer.", "danger")
            return render_template('inscription_etape2.html')

        # Fusionner les données de l'étape 1 et 2
        step1_data = session.get('registration_step1_data', {})
        full_user_data = {
            **step1_data, # Opérateur de décomposition de dictionnaire
            'postnom': request.form.get('middle_name'),
            'naissance': request.form.get('naissance'),
            'adresse': request.form.get('adresse'),
            'nom_boutique': request.form.get('nom_boutique'),
            'description': request.form.get('description')
        }

        # Appeler le service de traitement avec les données complètes
        if process_registration(full_user_data):
            session.pop('registration_step1_data', None) # Nettoyer la session
            return redirect(url_for('auth.verify')) # Rediriger vers la vérification OTP
        else:
            # Si le service a flashé une erreur (ex: email déjà pris), on reste sur l'étape 2
            return render_template('inscription_etape2.html')
            
    return render_template('inscription_etape2.html')

@auth_bp.route('/verify')
def verify():
    otp_data = session.get('otp')
    if not otp_data:
        return redirect(url_for('auth.inscription'))
    
    email = session.get('pending_user', {}).get('email')
    return render_template('verify.html', expires_at=otp_data['expires_at'], email=email)

@auth_bp.route('/valider_otp', methods=['POST'])
def valider_otp():
    submitted_code = request.form.get('code')
    result = process_otp_validation(submitted_code)

    if result == "success":
        flash('Compte créé avec succès !', 'success')
        return redirect(url_for('auth.connexion'))
    elif result == "incorrect_code":
        attempts_left = 3 - session.get('otp', {}).get('attempts', 3)
        flash(f"Code incorrect. Tentatives restantes : {attempts_left}", "danger")
        return redirect(url_for('auth.verify'))
    elif result == "expired_or_max_attempts":
        flash("Code expiré ou trop de tentatives.", "danger")
        return redirect(url_for('auth.inscription'))
    elif result == "redirect_register":
        return redirect(url_for('auth.inscription'))
    return redirect(url_for('auth.inscription')) # Fallback

@auth_bp.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()

        try:
            redis = get_redis_client()
            # Clé Redis unique pour suivre les tentatives de cet email
            attempt_key = f"login_attempts:{email}"

            # --- DÉBUT DE LA PROTECTION FORCE BRUTE ---
            # 1. Vérifier si le compte est actuellement verrouillé
            remaining_time = redis.ttl(attempt_key)
            if remaining_time > 0:
                minutes_left = int(remaining_time / 60)
                flash(f"Trop de tentatives échouées. Compte bloqué pour encore {minutes_left} minutes.", 'danger')
                return render_template('connexion.html')
        except RedisConnectionError:
            current_app.logger.critical("CRITICAL: Could not connect to Redis. Brute-force protection is disabled.")
            redis = None # On s'assure que redis est None pour la suite

        user = User.get_by_email(email)

        if user and bcrypt.check_password_hash(user.password, password):
            # 2. En cas de succès, on réinitialise le compteur
            if redis:
                redis.delete(attempt_key)
            login_user(user, remember=True) # <-- MODIFICATION : Utilise la durée de vie de la session
            # On initialise le timer d'inactivité
            session['last_activity_time'] = time.time()
            return redirect(url_for('auth.index'))
        else:
            # 3. En cas d'échec, on incrémente le compteur
            if redis:
                # Incrémente le compteur et vérifie s'il atteint la limite
                current_attempts = redis.incr(attempt_key)
                if current_attempts >= MAX_ATTEMPTS:
                    # Si la limite est atteinte, on bloque le compte pour 15 minutes
                    redis.expire(attempt_key, LOCKOUT_PERIOD_SECONDS)
            flash('Identifiants incorrects', 'danger')
    return render_template('connexion.html')
@auth_bp.route('/index')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.nom_boutique 
        FROM produits p 
        JOIN users u ON p.seller_id = u.id
        """)
    produits = cursor.fetchall()
    random.shuffle(produits)
    cursor.close()
    conn.close()
    claims = current_user.get_claims()
    
    return render_template(
        "index.html",
        name=claims.get("first_name"),
        produits=produits,
        user=claims
    )
@auth_bp.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.connexion'))