from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ext import bcrypt
from profils.models import Buyer
from profils.models import Seller

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
        profil_file = request.files.get("profil")

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

  
    cart_items, total = Buyer.get_panier(current_user.id)
    

    buyer_obj = Buyer.get_by_id(current_user.id)
    

    user_info = buyer_obj.get_claims() if buyer_obj else {}
    
    return render_template("profil_acheteur.html", user=user_info, cart_items=cart_items, cart_total=total)


seller_bp = Blueprint('seller', __name__)



@seller_bp.route("/seller_dashboard")
@login_required
def seller_dashboard():
    produits = Seller.get_produits(current_user.id)
    seller_obj = Seller.get_by_id(current_user.id)
    

    user_info = seller_obj.get_claims() if seller_obj else {}
    return render_template("profil_vendeur.html", user=user_info, produits=produits)
