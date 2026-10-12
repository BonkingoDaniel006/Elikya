from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ext import bcrypt
from profils.models import Buyer
from profils.models import Seller
from services.pagination import parse_cursor

buyer_bp = Blueprint('buyer', __name__)

@buyer_bp.route("/profil_acheteur", methods=["GET", "POST"])
@login_required
def profil_acheteur():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        prenom = request.form.get("prenom")
        nom = request.form.get("nom")
        postnom = request.form.get("postnom")
        adresse = request.form.get("adresse")
        new_password = request.form.get("new_password")
        profil_file = request.files.get("profil") # Le champ pour la nouvelle image de profil

        if not Buyer.verifier_mot_de_passe(current_user.id, current_password, bcrypt):
            flash("Mot de passe actuel incorrect. Modification annulée.", "danger")
            return redirect(url_for('buyer.profil_acheteur'))

        hashed_new_password = None
        if new_password and new_password.strip() != "":
            hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        success = Buyer.modifier(
            id=current_user.id,
            prenom=prenom,
            nom=nom,
            postnom=postnom,
            profil=profil_file,
            adresse=adresse,
            hashed_new_password=hashed_new_password
        )

        if success:
            flash("Votre profil a été mis à jour avec succès !", "success")
        else:
            flash("Une erreur est survenue lors de la mise à jour.", "danger")

        return redirect(url_for('buyer.profil_acheteur'))

    buyer_obj = Buyer.get_by_id(current_user.id)
    

    user_info = buyer_obj.get_claims() if buyer_obj else {}
    
    return render_template(
        "profil_acheteur.html",
        user=user_info,
    )


seller_bp = Blueprint('seller', __name__, template_folder='.')



@seller_bp.route("/seller_dashboard")
@login_required
def seller_dashboard():
    produits, produits_next_cursor = Seller.get_produits_page(
        current_user.id,
        after_id=parse_cursor(request.args.get("products_after"))
    )
    commandes, commandes_next_cursor = Seller.get_commandes_page(
        current_user.id,
        after_id=parse_cursor(request.args.get("orders_after"))
    )
    notifications, notifications_next_cursor = Seller.get_for_user_page(
        current_user.id,
        after_id=parse_cursor(request.args.get("notifications_after"))
    )
    seller_obj = Seller.get_by_id(current_user.id)
    

    user_info = seller_obj.get_claims() if seller_obj else {}
    return render_template(
        "seller_dash.html",
        user=user_info,
        produits=produits,
        produits_next_cursor=produits_next_cursor,
        commandes=commandes,
        commandes_next_cursor=commandes_next_cursor,
        notifications=notifications,
        notifications_next_cursor=notifications_next_cursor
    )
