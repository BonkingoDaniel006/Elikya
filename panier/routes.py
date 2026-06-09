from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail, csrf, get_db_connection
from panier.models import Panier, Commande
from profils.models import Buyer
from payment_service import create_payment
import uuid
import stripe
from datetime import datetime, timedelta
import os

panier_bp = Blueprint('panier', __name__)

@panier_bp.route("/panier")
@login_required
def panier():
    cart_items, total = Panier.get_panier(current_user.id)
    user_info = current_user.get_claims()
    return render_template("paiement.html", user=user_info, cart_items=cart_items, cart_total=total)

@panier_bp.route("/process_payment", methods=["POST"])
@login_required
def process_payment():
    payment_method = request.form.get("payment")
    user_id = current_user.id

    if payment_method in ["orange-money", "airtel-money", "mpesa"]:
        return redirect(url_for("panier.mobile_money", method=payment_method))
    
    if payment_method == "card":
        stripe.api_key = os.getenv("cle_secrete")
        cart_items, total = Panier.get_panier(user_id)
        if not cart_items:
            flash("Votre panier est vide.", "warning")
            return redirect(url_for('panier.panier'))

        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item['product_name']},
                    'unit_amount': int(float(item['product_price']) * 100),
                },
                'quantity': item['quantite'],
            })

        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode='payment',
                success_url=url_for('panier.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('panier.cancel', _external=True),
                metadata={'buyer_id': str(user_id)}
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            flash(f"Erreur Stripe: {str(e)}", "danger")
            return redirect(url_for('panier.panier'))

    return f"<h1>Paiement via {payment_method}</h1><p>L'API pour ce moyen de paiement sera intégrée ici.</p>"

@panier_bp.route("/mobile_money")
@login_required
def mobile_money():
    method = request.args.get('method', 'Mobile Money')
    user_info = current_user.get_claims()
    return render_template("mobile_money.html", method=method, user=user_info)

@panier_bp.route("/initiate_mobile_payment", methods=["POST"])
@login_required
def initiate_mobile_payment():
    user_id = current_user.id
    phone = request.form.get("phone")
    payment_intent_id = str(uuid.uuid4())
    
    cart_items, total_amount = Panier.get_panier(user_id)
    if not cart_items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('panier.panier'))

    buyer = Buyer.get_by_id(user_id)
    adresse = buyer.adresse if buyer else "Non spécifiée"
    
    date_reception = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    date_livraison = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    commande_data = []
    for item in cart_items:
        commande_data.append((
            item['id'], user_id, buyer.prenom, buyer.nom, adresse,
            item['product_id'], item['product_name'], item['product_price'],
            item['product_description'], item['product_image_url'],
            item['seller_id'], item['seller_name'], item['quantite'],
            item['prix_total'], date_reception, date_livraison, "16:00", 2.5,
            "En attente", payment_intent_id
        ))

    try:
        res = create_payment(phone, total_amount, reference_id=payment_intent_id)
        if "error" not in res and res.get("status") != "failed":
            Commande.create(commande_data)
            return render_template('attente_paiement.html', reference_id=payment_intent_id, method=request.form.get("method", "Mobile Money"))
        else:
            flash(f"Erreur Shwary: {res.get('error', 'Échec de l\'initiation')}", "danger")
    except Exception as e:
        flash(f"Erreur de connexion: {str(e)}", "danger")
    
    return redirect(url_for('panier.panier'))

@panier_bp.route('/api/callback', methods=['POST'])
@csrf.exempt
def shwary_callback():
    data = request.get_json(silent=True)
    if not data or str(data.get("userId")) != str(current_app.config['SHWARY_MERCHANT_ID']):
        return jsonify({"error": "Unauthorized"}), 401

    reference_id = data.get("referenceId") or data.get("referenceID")
    status = data.get("status")
    amount_received = data.get("amount")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT SUM(CAST(prix_total AS DECIMAL(10,2))) as total, buyer_id FROM commande WHERE payment_intent_id = %s", (reference_id,))
        order_data = cursor.fetchone()

        if not order_data or not order_data['total']:
            return jsonify({"error": "Order not found"}), 404

        if status == "success" and round(float(amount_received), 2) >= round(float(order_data['total']), 2):
            Commande.update_status(reference_id, "True")
            Panier.clear_panier(order_data['buyer_id'])
            return jsonify({"status": "updated"}), 200
        else:
            Commande.update_status(reference_id, "Echoué")
            return jsonify({"status": "failed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@panier_bp.route("/api/check_status/<payment_intent_id>")
@login_required
def check_status(payment_intent_id):
    status_data = Commande.check_status(payment_intent_id)
    if status_data:
        return jsonify({"status": status_data['etat']})
    return jsonify({"status": "not_found"}), 404

@panier_bp.route("/paiement_finalise")
@login_required
def paiement_finalise():
    user_info = current_user.get_claims()
    return render_template('paiement confirmé.html', user=user_info)

@panier_bp.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    if session_id:
        stripe.api_key = os.getenv("cle_secrete")
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            if checkout_session.payment_status == 'paid':
                buyer_id = checkout_session.metadata.get('buyer_id')
                if buyer_id:
                    Panier.clear_panier(buyer_id)
        except Exception:
            pass
    user_info = current_user.get_claims()
    return render_template('paiement confirmé.html', user=user_info)

@panier_bp.route('/cancel')
def cancel():
    flash("Le paiement a été annulé.", "info")
    return redirect(url_for('panier.panier'))
