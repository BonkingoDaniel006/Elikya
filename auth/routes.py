from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from ext import bcrypt, mail
from auth.models import User
import secrets
import time

auth_bp = Blueprint('auth', __name__)

def generer_code_verification(longueur=6):
    return "".join(secrets.choice("0123456789") for _ in range(longueur))

@auth_bp.route('/')
def racine():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    return redirect(url_for('auth.inscription'))

@auth_bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        # Collecte des données sans insertion immédiate
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
        
        # Logique de l'architecte : génération OTP et stockage session
        verification = generer_code_verification()
        session['otp'] = {
            'code': verification,
            'expires_at': time.time() + 120,
            'attempts': 0
        }
        session['pending_user'] = user_data

        # Envoi de l'email
        msg = Message("Code de vérification Elikya", 
                      sender=current_app.config['MAIL_USERNAME'], 
                      recipients=[user_data['email']])
        msg.body = f"Bonjour {user_data['prenom']},\n\nVotre code de vérification est : {verification}\nCe code expirera dans 2 minutes."
        mail.send(msg)
        
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
        # Hashage et insertion finale
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
    return render_template('index.html', user=current_user)
@auth_bp.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.connexion'))