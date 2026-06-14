from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail, get_db_connection
from auth.models import User
from produits.models import Add_panier
from produits.models import Details_produit
from produits.models import Ajouter_produit
from produits.models import Suprimer_produit
from produits.models import Modifier_produit



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


@produit_bp.route("/ajouter_produit", methods=["GET", "POST"])
@login_required
def ajouter_produit():
    # user_info est déjà garanti par @login_required
    user_info = current_user.get_claims()

    if request.method == "GET":
        return render_template("ajouter_produit.html", user=user_info)

    # Récupération des données du formulaire
    name = request.form.get("nom_produit")
    price = request.form.get("prix")
    description = request.form.get("description")
    # On récupère le FICHIER et non le texte
    image_file = request.files.get("image_url")
    seller_id = user_info.get("id")

    result = Ajouter_produit.ajouter(
        id=None, 
        seller_id=seller_id, 
        name=name, 
        price=price, 
        description=description, 
        image_url=image_file)

    # Vérification si le modèle a renvoyé une erreur (ex: format non autorisé)
    if isinstance(result, tuple) and len(result) == 2:
        flash(result[0], "danger")
        return redirect(url_for('produit.ajouter_produit'))

    flash("Produit ajouté avec succès !", "success")
    return redirect(url_for('seller.seller_dashboard'))


@produit_bp.route("/suprimer_produit/<int:product_id>", methods=["GET", "POST"])
@login_required
def suprimer_produit(product_id):
    # 1. Vérification de l'existence du produit
    produit = Details_produit.get_by_id(product_id)
    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('seller.seller_dashboard'))

    user_info = current_user.get_claims()
    # 2. Sécurité : Vérifier que l'utilisateur est bien le propriétaire
    if produit.seller_id != user_info.get('id'):
        flash("Action non autorisée.", "danger")
        return redirect(url_for('seller.seller_dashboard'))

    if request.method == "GET":
        # Redirection vers le dashboard avec un paramètre pour déclencher la modale de confirmation
        return redirect(url_for('seller.seller_dashboard', confirm_delete=product_id))

    # 3. POST : Vérification du mot de passe avant suppression
    password = request.form.get("password")
    user_db = User.get_by_id(current_user.id)

    if password and bcrypt.check_password_hash(user_db.password, password):
        Suprimer_produit.supprimer(product_id)
        flash("Le produit a été supprimé avec succès.", "success")
    else:
        flash("Mot de passe incorrect. Suppression annulée.", "danger")

    return redirect(url_for('seller.seller_dashboard'))


@produit_bp.route("/modifier_produit/<int:product_id>", methods=["GET", "POST"])
@login_required
def modifier_produit(product_id):
    produit = Details_produit.get_by_id(product_id)
    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('seller.seller_dashboard'))

    user_info = current_user.get_claims()
    if produit.seller_id != user_info.get('id'):
        flash("Action non autorisée.", "danger")
        return redirect(url_for('seller.seller_dashboard'))

    if request.method == "GET":
        # On pourrait aussi déclencher une modale de modification ici
        return redirect(url_for('seller.seller_dashboard', update_product=product_id))
    
    # Récupération des données pour la modification (exemple avec nom et prix)
    name = request.form.get("nom_produit")
    price = request.form.get("prix")
    description = request.form.get("description")
    image_file = request.files.get("image_url")  # Récupération du fichier image
    password = request.form.get("password")
    
    user_db = User.get_by_id(current_user.id)

    if password and bcrypt.check_password_hash(user_db.password, password):
        # On passe les nouvelles données au modèle
        result = Modifier_produit.modifier(
            id=product_id, 
            seller_id=user_info.get("id"), 
            name=name, 
            price=price, 
            description=description, 
            image_url=image_file
        )

        # Vérification si le modèle a renvoyé une erreur de format de fichier
        if isinstance(result, tuple) and len(result) == 2:
            flash(result[0], "danger")
            return redirect(url_for('seller.seller_dashboard'))

        flash("Le produit a été modifié avec succès.", "success")
    else:
        flash("Mot de passe incorrect. Modification annulée.", "danger")

    return redirect(url_for('seller.seller_dashboard'))