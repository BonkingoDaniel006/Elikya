import html
import secrets
import time
from flask import current_app, session, flash
import re
from redis.exceptions import RedisError
from auth.models import User
from ext import bcrypt
from services.email_queue import EmailQueueUnavailable, enqueue_email

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

def _enqueue_otp_email(email_destinataire, prenom, code_otp):
    """Place l'envoi de l'OTP en file pour ne pas bloquer la requête d'inscription."""
    safe_prenom = html.escape(prenom or "")
    html_content = f"""
        <h3>Bonjour {safe_prenom},</h3>
        <p>Votre code de vérification unique est : <strong>{code_otp}</strong></p>
        <p>Ce code expirera dans 20 minutes.</p>
    """
    enqueue_email(
        to=email_destinataire,
        subject="Code de vérification Elikya",
        html_content=html_content,
    )

def process_registration(form_data):
    """Traite une nouvelle demande d'inscription."""
    # 1. Valider la complexité du mot de passe
    password_error = _validate_password(form_data['password'])
    if password_error:
        flash(password_error, 'danger')
        return False

    verification_code = _generer_code_verification()
    try:
        _enqueue_otp_email(
            form_data['email'],
            form_data['prenom'],
            verification_code,
        )
    except (EmailQueueUnavailable, RedisError):
        current_app.logger.exception("Impossible de placer l'email OTP dans la file.")
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