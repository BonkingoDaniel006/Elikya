from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
# Plus besoin de flask_mail ici !
from ext import bcrypt  # 'mail' a été retiré s'il n'est plus utilisé ailleurs
from auth.models import User
from feed.models import Produits
import secrets
import time
import requests  # Ajout de requests pour l'API Brevo
import os

auth_bp = Blueprint('auth', __name__)

def generer_code_verification(longueur=6):
    return "".join(secrets.choice("0123456789") for _ in range(longueur))

def envoyer_otp_brevo(email_destinataire, prenom, code_otp):
    """Fonction utilitaire pour envoyer l'OTP via l'API HTTP de Brevo"""
    url = "https://api.brevo.com/v3/smtp/email"
    
    
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        current_app.logger.error("La variable d'environnement BREVO_API_KEY n'est pas configurée.")
        return False

    payload = {
        
        "sender": {"name": "Elikya", "email": "bokingopro.com"}, 
        "to": [{"email": email_destinataire}],
        "subject": "Code de vérification Elikya",
        "htmlContent": f"""
            <h3>Bonjour {prenom},</h3>
            <p>Votre code de vérification unique est : <strong>{code_otp}</strong></p>
            <p>Ce code expirera dans 2 minutes.</p>
        """
    }
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    try:
        
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 201:
            return True
        else:
            current_app.logger.error(f"Erreur de l'API Brevo ({response.status_code}) : {response.text}")
            return False
    except Exception as e:
        current_app.logger.error(f"Exception lors de l'envoi HTTP à Brevo : {str(e)}")
        return False

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

        if User.get_by_email(user_data['email']):
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('auth.inscription'))
        
        verification = generer_code_verification()
        session['otp'] = {
            'code': verification,
            'expires_at': time.time() + 1200,
            'attempts': 0
        }
        session['pending_user'] = user_data

        
        email_envoye = envoyer_otp_brevo(
            email_destinataire=user_data['email'], 
            prenom=user_data['prenom'], 
            code_otp=verification
        )

        if not email_envoye:
            flash("Le service d'envoi d'emails est temporairement indisponible. Veuillez réessayer plus tard.", "danger")
            return redirect(url_for('auth.inscription'))
        
        return redirect(url_for('auth.verify'))
            
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
    otp_data = session.get('otp')
    pending_user = session.get('pending_user')
    
    if not otp_data or not pending_user:
        return redirect(url_for('auth.inscription'))

    if time.time() > otp_data['expires_at'] or otp_data['attempts'] >= 3:
        session.pop('otp', None)
        flash("Code expiré ou trop de tentatives.", "danger")
        return redirect(url_for('auth.inscription'))

    if request.form.get('code') == otp_data['code']:
        hashed_pw = bcrypt.generate_password_hash(pending_user['password']).decode('utf-8')
        User.create_user(pending_user, hashed_pw)
        session.pop('otp', None)
        session.pop('pending_user', None)
        flash('Compte créé avec succès !', 'success')
        return redirect(url_for('auth.connexion'))

    otp_data['attempts'] += 1
    session['otp'] = otp_data
    flash(f"Code incorrect. Tentatives restantes : {3 - otp_data['attempts']}", "danger")
    return redirect(url_for('auth.verify'))

@auth_bp.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        user = User.get_by_email(email)

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('auth.index'))
        else:
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