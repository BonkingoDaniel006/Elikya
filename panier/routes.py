from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail
from panier.models import Panier

panier_bp = Blueprint('panier', __name__)

@panier_bp.route("/panier")
@login_required
def panier():
    cart_items, total = Panier.get_panier(current_user.id)

    user_info = current_user.get_claims()

    return render_template ("paiement.html", user=user_info, cart_items=cart_items, cart_total=total )




