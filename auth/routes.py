from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
import time
from ext import bcrypt
from auth.models import User
from feed.models import Produits
from auth.services import process_registration, process_otp_validation

auth_bp = Blueprint('auth', __name__)

# --- Configuration de la protection contre la force brute ---
# Dictionnaire pour stocker les tentatives échouées en mémoire.
# Format: {'email': {'failures': count, 'last_attempt': timestamp}}
login_attempts = {}
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
        # Vérifier si la politique de confidentialité a été acceptée
        if 'privacy_policy' not in request.form:
            flash("Vous devez accepter la politique de confidentialité pour continuer.", "danger")
            return redirect(url_for('auth.inscription'))

        # Ajout de la vérification de la confirmation du mot de passe
        if request.form['password'] != request.form['confirm_password']:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for('auth.inscription'))

        user_data = {
            'nom': request.form['last_name'],
            'prenom': request.form['first_name'],
            'postnom': request.form['middle_name'],
            'email': request.form['email'],
            'naissance': request.form['naissance'],
            'adresse': request.form['adresse'],
            'nom_boutique': request.form['nom_boutique'],
            'description': request.form['description'],
            'password': request.form['password']
        }

        if process_registration(user_data):
            # S'il n'y a pas d'erreur, on continue vers la vérification OTP
            return redirect(url_for('auth.verify'))
        else:
            # S'il y a une erreur, le service a déjà "flashé" le message. On redirige.
            return redirect(url_for('auth.inscription'))
            
    return render_template('inscription.html')

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

        # --- DÉBUT DE LA PROTECTION FORCE BRUTE ---
        # 1. Vérifier si le compte est actuellement verrouillé
        if email in login_attempts:
            user_attempts = login_attempts[email]
            if user_attempts['failures'] >= MAX_ATTEMPTS:
                time_since_last_attempt = time.time() - user_attempts['last_attempt']
                if time_since_last_attempt < LOCKOUT_PERIOD_SECONDS:
                    remaining_time = int((LOCKOUT_PERIOD_SECONDS - time_since_last_attempt) / 60)
                    flash(f"Trop de tentatives échouées. Compte bloqué pour encore {remaining_time} minutes.", 'danger')
                    return render_template('connexion.html')
                else:
                    # Si la période de blocage est terminée, on réinitialise
                    login_attempts.pop(email, None)

        user = User.get_by_email(email)

        if user and bcrypt.check_password_hash(user.password, password):
            # 2. En cas de succès, on réinitialise le compteur
            login_attempts.pop(email, None)
            login_user(user)
            return redirect(url_for('auth.index'))
        else:
            # 3. En cas d'échec, on incrémente le compteur
            if email not in login_attempts:
                login_attempts[email] = {'failures': 0, 'last_attempt': 0}
            login_attempts[email]['failures'] += 1
            login_attempts[email]['last_attempt'] = time.time()
            flash('Identifiants incorrects', 'danger')
    return render_template('connexion.html')
@auth_bp.route('/index')
@login_required
def index():
    produits = Produits.get_all()
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