from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app

feed_bp = Blueprint('feed', __name__)

@feed_bp.route("/")
def index():
    """Redirige la racine vers la page d'accueil principale."""
    return redirect(url_for('auth.index'))
