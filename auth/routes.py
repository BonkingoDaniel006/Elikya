from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
import random
from datetime import datetime, date
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

    # Déterminer l'étape actuelle en fonction de la progression dans la session
    if 'registration_step3_data' in session:
        step = 'etape4'
    elif 'registration_step2_data' in session:
        step = 'etape3'
    elif 'registration_step1_data' in session:
        step = 'etape2'
    else:
        step = 'etape1'

    if request.method == 'POST':
        # --- Étape 1: Nom et Email ---
        if 'email' in request.form:
            email = request.form['email']
            if User.get_by_email(email):
                flash('Cet email est déjà utilisé. Veuillez en choisir un autre.', 'danger')
                return render_template('inscription_etape1.html')

            session['registration_step1_data'] = {
                'nom': request.form['last_name'],
                'prenom': request.form['first_name'],
                'email': email
            }
            return redirect(url_for('auth.inscription'))

        # --- Étape 2: Date de naissance ---
        elif 'naissance' in request.form:
            try:
                dob_str = request.form['naissance']
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if age < 13:
                    flash("Vous devez avoir au moins 13 ans pour vous inscrire.", "danger")
                    return render_template('inscription_etape2.html')
            except ValueError:
                flash("Date de naissance invalide.", "danger")
                return render_template('inscription_etape2.html')

            step1_data = session.get('registration_step1_data', {})
            session['registration_step2_data'] = {
                **step1_data,
                'postnom': request.form.get('middle_name'),
                'naissance': dob_str,
                'adresse': request.form.get('adresse')
            }
            return redirect(url_for('auth.inscription'))

        # --- Étape 3: Boutique (Optionnel) ---
        elif 'nom_boutique' in request.form:
            step2_data = session.get('registration_step2_data', {})
            session['registration_step3_data'] = {
                **step2_data,
                'nom_boutique': request.form.get('nom_boutique'),
                'description': request.form.get('description')
            }
            return redirect(url_for('auth.inscription'))

        # --- Étape 4: Mot de passe et finalisation ---
        elif 'password' in request.form:
            if request.form['password'] != request.form['confirm_password']:
                flash("Les mots de passe ne correspondent pas.", "danger")
                return render_template('inscription_etape4.html')

            step3_data = session.get('registration_step3_data', {})
            full_user_data = {
                **step3_data,
                'password': request.form['password']
            }

            if process_registration(full_user_data):
                session.pop('registration_step3_data', None)
                session.pop('registration_step1_data', None)
                session.pop('registration_step2_data', None)
                return redirect(url_for('auth.verify'))
            else:
                # process_registration flashera l'erreur (ex: complexité mdp)
                return render_template('inscription_etape3.html')

    # Affichage de la bonne page en fonction de l'étape
    if step == 'etape4':
        return render_template('inscription_etape4.html')
    if step == 'etape3':
        return render_template('inscription_etape3.html')
    if step == 'etape2':
        return render_template('inscription_etape2.html')
    return render_template('inscription_etape1.html')

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