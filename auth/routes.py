from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt
from auth.models import User

auth_bp = Blueprint('auth', __name__)

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
        nom = request.form['last_name']
        prenom = request.form['first_name']
        postnom = request.form['middle_name']
        email = request.form['email']
        naissance = request.form['naissance']
        adresse = request.form['adresse']
        nom_boutique = request.form['nom_boutique']
        description = request.form['description']
        password = request.form['password']
        
        if not email or not password:
            flash('Veuillez remplir tous les champs', 'danger')
            return redirect(url_for('auth.inscription'))
        if User.get_by_email(email):
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('auth.inscription'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = User.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (prenom, nom, postnom, email, naissance, password, description, adresse, nom_boutique) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (prenom, nom, postnom, email, naissance, hashed_password, description, adresse, nom_boutique))
            conn.commit()
            flash('Inscription réussie !', 'success')
            return redirect(url_for('auth.connexion'))
        except Exception as e:
            conn.rollback()
            flash(f'Erreur lors de l\'inscription : {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('inscription.html')
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