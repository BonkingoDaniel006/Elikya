import logging

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from ext import csrf, get_db_connection
from panier.models import Panier, Commande, Suprimer_panier, Modifier_panier
from services.payment_service import initiate_remote_payment

# Configuration d'un logger si ce n'est pas déjà fait
logger = logging.getLogger(__name__)

panier_bp = Blueprint('panier', __name__)

# --- ROUTES D'AFFICHAGE ---

@panier_bp.route("/mes-commandes")
@login_required
def mes_commandes():
    """Affiche l'historique des commandes de l'utilisateur."""
    # --- DONNÉES FACTICES POUR LE DÉVELOPPEMENT ---
    # Cette section remplace l'appel à la base de données pour éviter l'erreur.
    commandes = [
        {
            'id': 101,
            'product_name': 'Casque Gamer Pro X',
            'product_image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=2070&auto=format&fit=crop',
            'date_creation': datetime.now() - timedelta(days=2),
            'etat': 'Livree'
        },
        {
            'id': 102,
            'product_name': 'Smartphone Elikya S24',
            'product_image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1780&auto=format&fit=crop',
            'date_creation': datetime.now() - timedelta(hours=5),
            'etat': 'Expediee'
        },
        {
            'id': 103,
            'product_name': 'Appareil Photo Vintage',
            'product_image_url': 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?q=80&w=2070&auto=format&fit=crop',
            'date_creation': datetime.now() - timedelta(minutes=30),
            'etat': 'En attente'
        }
    ]
    return render_template("commandes_acheteur.html", commandes=commandes, user=current_user.get_claims())

@panier_bp.route("/panier", methods=["GET", "POST"])
@login_required
def panier():
    """Affiche le panier de l'utilisateur."""
    cart_items, total = Panier.get_panier(current_user.id)

    if request.method == "POST":
        payment_method = request.form.get("payment")
        if payment_method in ["orange-money", "airtel-money", "mpesa"]:
            # Stocker les informations essentielles dans la session
            session['payment_info'] = {
                'cart_total': total,
                'method': payment_method
            }
            return redirect(url_for('panier.mobile_money_payment'))
        elif payment_method == "cash":
            # La logique pour le paiement à la livraison reste ici
            # (ou est déplacée vers sa propre fonction)
            pass # Mettez ici la logique pour le paiement cash

    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template("paiement.html", user=user_info, cart_items=cart_items, cart_total=total)


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

@panier_bp.route("/supprimer_article/<int:cart_id>", methods=["POST"])
@login_required
def supprimer_article(cart_id):
    """Supprime définitivement un article du panier."""
    Suprimer_panier.supprimer(cart_id, current_user.id)
    # Pour une API, on renvoie une réponse JSON plutôt qu'un message flash
    return jsonify({"message": "Article retiré du panier."}), 200

@panier_bp.route("/paiement/mobile", methods=["GET", "POST"])
@login_required
def mobile_money_payment():
    """Affiche le formulaire pour le paiement mobile et traite la soumission."""
    payment_info = session.get('payment_info')
    if not payment_info:
        flash("Session de paiement expirée ou invalide.", "warning")
        return redirect(url_for('panier.panier'))
        
    # On récupère les informations de l'utilisateur pour les passer au template
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}

    if request.method == "POST":
        # --- RÉCUPÉRATION ET SÉCURISATION DU MONTANT ---
        cart_total = payment_info.get('cart_total', 0)
        # Force un montant de test minimal si le panier est vide ou trop bas pour le test de production
        amount = float(cart_total) if float(cart_total) >= 2900 else 3000.0

        # --- NORMALISATION DU NUMÉRO DE TÉLÉPHONE ---
        phone_number = request.form.get("phone")
        normalized_phone = "".join(filter(str.isdigit, phone_number or ""))

        if normalized_phone.startswith("243"):
            normalized_phone = "0" + normalized_phone[3:]

        current_app.logger.info(f"Paiement envoyé au microservice -> Numéro: {normalized_phone}, Montant: {amount}")
        if not phone_number:
            flash("Le numéro de téléphone est requis.", "danger")
            return render_template("mobile_money.html", method=payment_info.get('method'), user=user_info)

        try:
            # Appel du service de paiement externe
            payment_response = initiate_remote_payment(phone=normalized_phone, amount=amount)
            transaction_id = payment_response.get("transaction_id")

            if not transaction_id:
                raise Exception("La réponse du service de paiement est invalide.")

            # Redirection vers la page d'attente avec l'ID de transaction
            return redirect(url_for('panier.attente_page', transaction_id=transaction_id))

        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'initiation du paiement : {e}")
            flash("Une erreur est survenue lors de l'initiation du paiement. Veuillez réessayer.", "danger")

    return render_template("mobile_money.html", method=payment_info.get('method'), user=user_info)

@panier_bp.route("/paiement/attente")
@login_required
def attente_page():
    """Page qui attend la confirmation du paiement mobile."""
    transaction_id = request.args.get('transaction_id')
    if not transaction_id:
        flash("ID de transaction manquant.", "danger")
        return redirect(url_for('panier.panier'))
    
    # Le template attente_paiement.html utilisera cet ID pour interroger le statut
    return render_template("attente_paiement.html", transaction_id=transaction_id)

@panier_bp.route("/paiement/resultat")
@login_required
def resultat_page():
    """Affiche le résultat de la transaction de paiement."""
    status = request.args.get('status')
    tx_id = request.args.get('tx_id')
    
    # Pour l'instant, on passe juste les infos au template.
    # Plus tard, on pourra créer la commande dans la DB ici.
    return render_template("resultat_paiement.html", status=status, transaction_id=tx_id)
