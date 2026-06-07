from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail
from profils.models import Buyer
from profils.models import Seller

buyer_bp = Blueprint('buyer', __name__)


@buyer_bp.route("/profil_acheteur")
@login_required
def profil_acheteur():
    # Récupération des items du panier et du total via la méthode de classe
    cart_items, total = Buyer.get_panier(current_user.id)
    
    # Utilisation des informations de l'utilisateur connecté (UserMixin)
    user_info = current_user.get_claims()
    
    return render_template("profil_acheteur.html", user=user_info, cart_items=cart_items, cart_total=total)

seller_bp = Blueprint('seller', __name__)



@seller_bp.route("/seller_dashboard")
@login_required
def seller_dashboard():
    produits = Seller.get_produits(current_user.id)
    user_info = current_user.get_claims()
    return render_template("profil_vendeur.html", user=user_info, produits=produits)
