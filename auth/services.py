import os
import secrets
import time
import requests
from flask import current_app, session, flash
import re
from auth.models import User
from ext import bcrypt

def _generer_code_verification(longueur=6):
    """Génère un code de vérification numérique sécurisé."""
    return "".join(secrets.choice("0123456789") for _ in range(longueur))

def _validate_password(password):
    """Vérifie la complexité du mot de passe et retourne un message d'erreur si invalide."""
    if len(password) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[A-Z]", password):
        return "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r"[a-z]", password):
        return "Le mot de passe doit contenir au moins une minuscule."
    if not re.search(r"\d", password):
        return "Le mot de passe doit contenir au moins un chiffre."
    if password.lower() in ['123456', 'password', 'azerty', 'qwerty']:
        return "Le mot de passe est trop simple."
    return None

def _envoyer_otp_brevo(email_destinataire, prenom, code_otp):
    """Fonction utilitaire pour envoyer l'OTP via l'API HTTP de Brevo"""
    url = "https://api.brevo.com/v3/smtp/email"
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        current_app.logger.error("La variable d'environnement BREVO_API_KEY n'est pas configurée.")
        return False

    payload = {
        "sender": {"name": "Elikya", "email": os.getenv("PROV_EMAIL")},
        "to": [{"email": email_destinataire}],
        "subject": "Code de vérification Elikya",
        "htmlContent": f"""
            <h3>Bonjour {prenom},</h3>
            <p>Votre code de vérification unique est : <strong>{code_otp}</strong></p>
            <p>Ce code expirera dans 20 minutes.</p>
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
            current_app.logger.info(f"OTP envoyé avec succès à {email_destinataire}")
            return True
        else:
            current_app.logger.error(f"Erreur de l'API Brevo ({response.status_code}) : {response.text}")
            return False
    except Exception as e:
        current_app.logger.error(f"Exception lors de l'envoi HTTP à Brevo : {str(e)}")
        return False

def process_registration(form_data):
    """Traite une nouvelle demande d'inscription."""
    # 1. Valider la complexité du mot de passe
    password_error = _validate_password(form_data['password'])
    if password_error:
        flash(password_error, 'danger')
        return False

    if User.get_by_email(form_data['email']):
        flash('Cet email est déjà utilisé', 'danger')
        return False

    verification_code = _generer_code_verification()
    if not _envoyer_otp_brevo(form_data['email'], form_data['prenom'], verification_code):
        flash("Le service d'envoi d'emails est indisponible. Veuillez réessayer plus tard.", "danger")
        return False

    session['otp'] = {'code': verification_code, 'expires_at': time.time() + 1200, 'attempts': 0}
    session['pending_user'] = form_data
    return True # Signifie "succès"

def process_otp_validation(submitted_code):
    """Valide le code OTP soumis par l'utilisateur."""
    otp_data = session.get('otp')
    pending_user = session.get('pending_user')

    if not otp_data or not pending_user:
        return "redirect_register"

    if time.time() > otp_data['expires_at'] or otp_data['attempts'] >= 3:
        session.pop('otp', None)
        return "expired_or_max_attempts"

    if submitted_code == otp_data['code']:
        hashed_pw = bcrypt.generate_password_hash(pending_user['password']).decode('utf-8')
        User.create_user(pending_user, hashed_pw)
        session.pop('otp', None)
        session.pop('pending_user', None)
        return "success"

    otp_data['attempts'] += 1
    session['otp'] = otp_data
    return "incorrect_code"