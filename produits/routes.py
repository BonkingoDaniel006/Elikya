from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail, get_db_connection
from produits.models import Add_panier
from produits.models import Details_produit


produit_bp = Blueprint('produit', __name__)

@produit_bp.route("/detail_produit/<int:product_id>")
def detail_produit(product_id):
    produit = Details_produit.get_by_id(product_id)
    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('feed.index'))
    
    # On ne récupère les claims que si l'utilisateur est connecté
    user_info = current_user.get_claims() if current_user.is_authenticated else None
    return render_template("detail_produit.html", produit=produit, user=user_info)


@produit_bp.route("/add_product/<int:product_id>", methods=["POST"])
@login_required
def add_panier(product_id):
    # 1. Récupération des infos utilisateur via Flask-Login
    user_info = current_user.get_claims()
    
    # 2. Récupération des détails du produit et du vendeur
    # On utilise le modèle existant pour éviter la duplication de code SQL
    produit = Details_produit.get_by_id(product_id)

    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('feed.index'))

    # 3. Validation de la quantité
    try:
        quantite = int(request.form.get("quantite", 1))
    except (ValueError, TypeError):
        quantite = 1

    if quantite <= 0:
        flash("Quantité invalide.", "warning")
        return redirect(url_for('produit.detail_produit', product_id=product_id))

    # 4. Calcul et enregistrement via le modèle
    prix_total = quantite * float(produit.price)
    
    Add_panier.create(
        buyer_id=user_info.get('id'),
        buyer_first_name=user_info.get('first_name'),
        buyer_last_name=user_info.get('last_name'),
        product_id=produit.id,
        product_name=produit.name,
        product_price=produit.price,
        product_description=produit.description,
        product_image_url=produit.image_url,
        seller_id=produit.seller_id,
        seller_name=produit.seller_name,
        quantite=quantite,
        prix_total=prix_total
    )
    
    flash(f"{produit.name} ajouté au panier !", "success")
    return redirect(url_for('produit.detail_produit', product_id=product_id))