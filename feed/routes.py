from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from feed.models import Produits

feed_bp = Blueprint('feed', __name__)

@feed_bp.route("/")
def index():
    """Affiche tous les produits sur le fil d'actualité"""
    produits = Produits.get_all()
    return render_template("index.html", produits=produits)
