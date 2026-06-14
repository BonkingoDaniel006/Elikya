from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from ext import csrf, get_db_connection
from panier.models import Panier, Commande, Suprimer_panier, Modifier_panier
from payment_service import create_payment
import uuid
from datetime import datetime, timedelta
from security import validate_phone_drc, normalize_phone_drc
from config import Config

panier_bp = Blueprint('panier', __name__)

# --- ROUTES D'AFFICHAGE ---

@panier_bp.route("/panier", methods=["GET", "POST"])
@login_required
def panier():
    """Étape 1 : Affichage du panier et choix de la méthode."""
    if request.method == "POST":
        method = request.form.get("payment")
        if method in ["orange-money", "airtel-money", "mpesa"]:
            return redirect(url_for('panier.mobile_money', method=method))
        
        flash("Cette méthode de paiement n'est pas encore disponible.", "warning")
        return redirect(url_for('panier.panier'))

    cart_items, total = Panier.get_panier(current_user.id)
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template("paiement.html", user=user_info, cart_items=cart_items, cart_total=total)

@panier_bp.route("/mobile_money")
@login_required
def mobile_money():
    """Étape 2 : Formulaire de saisie du numéro de téléphone."""
    method = request.args.get('method', 'mobile-money')
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template("mobile_money.html", method=method, user=user_info)

@panier_bp.route("/initiate_mobile_payment", methods=["POST"])
@login_required
def initiate_mobile_payment():
    """Étape 3 : Création de la commande 'en_attente' et envoi du Push USSD."""
    phone = request.form.get("phone")
    if not validate_phone_drc(phone):
        flash("Numéro de téléphone invalide (Format attendu: +243...).", "danger")
        return redirect(url_for('panier.mobile_money'))

    normalized_phone = normalize_phone_drc(phone)
    cart_items, total = Panier.get_panier(current_user.id)
    
    if not cart_items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('panier.panier'))

    reference_id = str(uuid.uuid4())
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}

    # Préparation des entrées pour la table commande
    order_entries = []
    for item in cart_items:
        order_entries.append((
            item.get('id'), current_user.id, user_info.get('prenom'), user_info.get('nom'),
            user_info.get('adresse', 'Kinshasa, RDC'), item.get('product_id'), item.get('product_name'),
            item.get('product_price'), item.get('product_description'), item.get('product_image_url'),
            item.get('seller_id'), item.get('seller_name'), item.get('quantite'), item.get('prix_total'),
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "16:00", 2.5, "en_attente", reference_id
        ))

    try:
        Commande.create(order_entries)
        # Appel Shwary pour déclencher le popup sur le téléphone
        res = create_payment(normalized_phone, total, reference_id=reference_id)

        if res.get("status") == "success" or "id" in res:
            # Redirection vers la page d'attente qui va poll l'API
            return render_template('attente_paiement.html', reference_id=reference_id)
        else:
            flash(f"Erreur Shwary : {res.get('error', 'Échec de l\'opération')}", "danger")
            return redirect(url_for('panier.panier'))
    except Exception as e:
        current_app.logger.error(f"Erreur paiement : {e}")
        flash("Une erreur technique est survenue.", "danger")
        return redirect(url_for('panier.panier'))

@panier_bp.route("/api/check_status/<payment_intent_id>")
@login_required
def check_status(payment_intent_id):
    """Route pour le polling JS : vérifie si le statut est passé à 'True'."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT etat FROM commande WHERE payment_intent_id = %s LIMIT 1", (payment_intent_id,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if order:
        return jsonify({"status": order['etat']})
    return jsonify({"status": "not_found"}), 404

@panier_bp.route("/paiement_finalise")
@login_required
def paiement_finalise():
    """Étape 4 : Affichage de la page de confirmation finale."""
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template('paiement confirmé.html', user=user_info)

@panier_bp.route('/api/callback', methods=['POST'])
@csrf.exempt
def shwary_callback():
    """Webhook Shwary : met à jour la commande et vide le panier si succès."""
    data = request.get_json(silent=True)
    if not data or str(data.get("userId")) != str(Config.SHWARY_MERCHANT_ID):
        return jsonify({"error": "Unauthorized"}), 401

    reference_id = data.get("referenceId")
    status = data.get("status")

    if status == "success":
        # Mise à jour de la commande et nettoyage du panier de l'acheteur
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT buyer_id FROM commande WHERE payment_intent_id = %s LIMIT 1", (reference_id,))
        order = cursor.fetchone()
        if order:
            Panier.clear_panier(order['buyer_id'])
            Commande.update_status(reference_id, "True") # 'True' est attendu par ton JS
        cursor.close()
        conn.close()
    else:
        Commande.update_status(reference_id, "Echoué")

    return jsonify({"status": "updated"}), 200

@panier_bp.route("/modifier_article/<int:cart_id>", methods=["POST"])
@login_required
def modifier_article(cart_id):
    """Met à jour la quantité et le prix total d'un article dans le panier."""
    try:
        quantite = int(request.form.get("quantite", 1))
        if quantite <= 0:
            return redirect(url_for('panier.supprimer_article', cart_id=cart_id))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT product_price FROM panier WHERE id = %s", (cart_id,))
        item = cursor.fetchone()
        cursor.close()
        conn.close()

        if item:
            prix_total = quantite * float(item['product_price'])
            Modifier_panier.modifier(cart_id, quantite, prix_total)
            flash("Panier mis à jour.", "success")
    except Exception as e:
        current_app.logger.error(f"Erreur modification panier: {e}")
        flash("Impossible de modifier la quantité.", "danger")

    return redirect(url_for('panier.panier'))

@panier_bp.route("/supprimer_article/<int:cart_id>", methods=["POST"])
@login_required
def supprimer_article(cart_id):
    """Supprime définitivement un article du panier."""
    Suprimer_panier.supprimer(cart_id)
    flash("Article retiré du panier.", "success")
    return redirect(url_for('panier.panier'))
