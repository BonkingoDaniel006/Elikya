import logging
from datetime import datetime, timedelta
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_required, current_user
from ext import csrf, get_db_connection
from notifications.models import Notification
from panier.models import Panier, Commande, Suprimer_panier, Modifier_panier
from services.security import validate_phone_drc, normalize_phone_drc
from services.payment_service import (
    create_payment,
    verify_transaction_api,
    ValidationError,
    AuthenticationError,
    ShwaryAPIError,
)
from config import Config

# Configuration d'un logger si ce n'est pas déjà fait
logger = logging.getLogger(__name__)

panier_bp = Blueprint('panier', __name__)

# --- ROUTES D'AFFICHAGE ---

@panier_bp.route("/panier", methods=["GET", "POST"])
@login_required
def panier():
    """Étape 1 : Affichage du panier et choix de la méthode."""
    if request.method == "POST":
        method = request.form.get("payment")
        if method in ["orange-money", "airtel-money", "mpesa"]:
            return redirect(url_for('panier.checkout', method=method))
        
        flash("Cette méthode de paiement n'est pas encore disponible.", "warning")
        return redirect(url_for('panier.panier'))

    cart_items, total = Panier.get_panier(current_user.id)
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template("paiement.html", user=user_info, cart_items=cart_items, cart_total=total)

logger = logging.getLogger(__name__)

@panier_bp.route("/mobile_money")
@panier_bp.route("/checkout")
@login_required
def checkout():
    """Étape 2 : Formulaire de paiement (à reconstruire)."""
    method = request.args.get('method')
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    cart_items, total = Panier.get_panier(current_user.id)

    if not cart_items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('panier.panier'))

    return render_template("mobile_money.html", method=method, user=user_info, cart_total=total)


@panier_bp.route("/initiate_mobile_payment", methods=["POST"])
@login_required
def initiate_mobile_payment():
    """
    Étape 3 : Lancement du processus de paiement Shwary.
    """
    phone = request.form.get("phone")
    if not validate_phone_drc(phone):
        flash("Numéro de téléphone invalide (Format attendu: +243...).", "danger")
        return redirect(url_for('panier.checkout', method=request.args.get('method')))

    normalized_phone = normalize_phone_drc(phone)
    cart_items, total = Panier.get_panier(current_user.id)
    
    if not cart_items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('panier.panier'))

    # 1. Générer une référence interne unique pour pré-enregistrer la commande
    internal_ref = str(uuid.uuid4())
    user_info = current_user.get_claims()
    order_entries = []
    for item in cart_items:
        order_entries.append((
            item.get('id'), user_info.get('id'), user_info.get('first_name'), user_info.get('last_name'),
            user_info.get('adresse', 'Non spécifiée'), item.get('product_id'), item.get('product_name'),
            item.get('product_price'), item.get('product_description'), item.get('product_image_url'),
            item.get('seller_id'), item.get('seller_name'), item.get('quantite'), item.get('prix_total'),
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "16:00", 2.5, "en_attente_paiement", internal_ref
        ))

    try:
        # 2. Insérer la commande en BDD avec le statut "en_attente_paiement"
        Commande.create(order_entries)
    except Exception as db_err:
        current_app.logger.error(f"Erreur BDD lors de la pré-création de commande: {db_err}")
        flash("Une erreur de base de données est survenue.", "danger")
        return redirect(url_for('panier.panier'))

    try:
        # 3. Appeler le service de paiement pour initier la transaction
        payment_response = create_payment(normalized_phone, total)
        shwary_tx_id = payment_response.get('id')

        # 4. Lier l'ID de transaction Shwary à notre commande
        Commande.link_shwary_transaction(internal_ref, shwary_tx_id)

        # 5. Rediriger vers la page d'attente avec l'ID de transaction
        return render_template('attente_paiement.html', reference_id=shwary_tx_id)

    except (ValidationError, AuthenticationError, ShwaryAPIError, Exception) as e:
        current_app.logger.error(f"Erreur lors de l'initiation du paiement Shwary : {e}")
        flash(f"Une erreur est survenue lors de l'initialisation du paiement : {e}", "danger")
        # On met à jour la commande pré-créée en 'echoue' pour ne pas la laisser en attente
        Commande.update_status(internal_ref, "echoue")
        return redirect(url_for('panier.panier'))


@panier_bp.route("/api/check_status/<reference_id>")
@login_required
def check_status(reference_id):
    """
    Route pour le polling JS : vérifie l'état de la commande dans la BDD.
    """
    try:
        order = Commande.get_order_by_shwary_tx(reference_id)
        if order:
            return jsonify({"status": order['etat']})
        return jsonify({"status": "not_found"}), 404
    except Exception as e:
        current_app.logger.error(f"Erreur check_status pour {reference_id}: {e}")
        return jsonify({"status": "error"}), 500


@panier_bp.route("/paiement_finalise")
@login_required
def paiement_finalise():
    """Étape 4 : Affichage de la page de confirmation finale."""
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template('paiement confirmé.html', user=user_info)


@panier_bp.route('/api/callback', methods=['POST'])
@csrf.exempt
def payment_callback():
    """
    Route de callback pour le service de paiement (webhook).
    La logique de traitement des webhooks de votre nouveau service ira ici.
    C'est l'URL que vous avez définie dans sdk.md et que Shwary appellera.
    """
    data = request.get_json(silent=True)
    current_app.logger.info(f"Webhook Shwary reçu : {data}")

    # 1. Vérifications de base du payload
    if not data or str(data.get("userId")) != str(Config.SHWARY_MERCHANT_ID):
        current_app.logger.warning("[WEBHOOK-SECURITY] UserID du payload invalide ou payload vide.")
        return jsonify({"error": "Unauthorized"}), 401

    tx_id = data.get("id")
    status = data.get("status")
    amount = data.get("amount")

    if not all([tx_id, status, amount]):
        return jsonify({"error": "Payload incomplet"}), 400

    # 2. Retrouver la commande dans notre BDD
    order = Commande.get_order_by_shwary_tx(tx_id)
    if not order:
        current_app.logger.warning(f"[WEBHOOK-ERROR] Commande introuvable pour la transaction Shwary {tx_id}.")
        return jsonify({"error": "Order not found"}), 404

    # 3. Vérifier la cohérence du montant
    if int(float(order['prix_total'])) != int(float(amount)):
        current_app.logger.error(f"[WEBHOOK-SECURITY] Montant incohérent pour tx {tx_id}. Attendu: {order['prix_total']}, Reçu: {amount}")
        return jsonify({"error": "Amount mismatch"}), 400

    # 4. Double confirmation via l'API (mesure de sécurité cruciale)
    try:
        if not verify_transaction_api(tx_id, status, amount):
            current_app.logger.critical(f"[WEBHOOK-SECURITY] Le statut du webhook ({status}) n'a pas pu être confirmé via l'API pour la tx {tx_id}.")
            return jsonify({"error": "Transaction not confirmed"}), 400
    except Exception as api_err:
        current_app.logger.error(f"[WEBHOOK-API-ERROR] Impossible de re-vérifier la tx {tx_id} : {api_err}")
        return jsonify({"error": "Verification failed"}), 500

    # 5. Traitement en fonction du statut
    if status == "completed":
        if order['etat'] == 'paye': # Éviter les traitements multiples
            return jsonify({"status": "already_processed"}), 200

        Commande.update_status(tx_id, "paye")
        buyer_id = Commande.get_buyer_id_from_ref(tx_id)
        if buyer_id:
            Panier.clear_panier(buyer_id)
            Notification.create(
                user_id=buyer_id,
                message=f"Votre paiement pour la commande (Réf: ...{str(tx_id)[-6:]}) a été accepté.",
                type='success'
            )
        current_app.logger.info(f"Paiement complété et traité pour la tx {tx_id}.")

    elif status in ["failed", "cancelled"]:
        Commande.update_status(tx_id, "echoue")
        buyer_id = Commande.get_buyer_id_from_ref(tx_id)
        if buyer_id:
            Notification.create(
                user_id=buyer_id,
                message=f"Votre paiement pour la commande (Réf: ...{str(tx_id)[-6:]}) a échoué.",
                type='danger')
        current_app.logger.warning(f"Paiement échoué pour la tx {tx_id}.")

    return jsonify({"status": "ok"}), 200

@panier_bp.route("/modifier_article/<int:cart_id>", methods=["PATCH"])
@login_required
def modifier_article(cart_id):
    """Met à jour la quantité et le prix total d'un article dans le panier."""
    try:
        quantite = int(request.form.get("quantite", 1))
        if quantite <= 0:
            # Si la quantité est 0 ou moins, on supprime l'article directement
            Suprimer_panier.supprimer(cart_id, current_user.id)
            flash("Article retiré du panier.", "success")
            return redirect(url_for('panier.panier'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # On vérifie que l'article appartient bien à l'utilisateur
        cursor.execute("SELECT product_price FROM panier WHERE id = %s AND buyer_id = %s", (cart_id, current_user.id))
        item = cursor.fetchone()

        if item:
            prix_total = quantite * float(item['product_price'])
            Modifier_panier.modifier(cart_id, quantite, prix_total)
            flash("Panier mis à jour.", "success")
    except Exception as e:
        current_app.logger.error(f"Erreur modification panier: {e}")
        flash("Impossible de modifier la quantité.", "danger")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

    return redirect(url_for('panier.panier'))

@panier_bp.route("/supprimer_article/<int:cart_id>", methods=["DELETE"])
@login_required
def supprimer_article(cart_id):
    """Supprime définitivement un article du panier."""
    Suprimer_panier.supprimer(cart_id, current_user.id)
    # Pour une API, on renvoie une réponse JSON plutôt qu'un message flash
    return jsonify({"message": "Article retiré du panier."}), 200
