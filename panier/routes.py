from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from ext import csrf, get_db_connection
from notifications.models import Notification
from panier.models import Panier, Commande, Suprimer_panier, Modifier_panier
from payment_service import initiate_payment_sdk, verify_transaction_api
import uuid
from datetime import datetime, timedelta
from services.security import validate_phone_drc, normalize_phone_drc
import secrets
from config import Config
import logging
from shwary import ValidationError, AuthenticationError, ShwaryAPIError, InsufficientFundsError, RateLimitingError

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
            return redirect(url_for('panier.mobile_money', method=method))
        
        flash("Cette méthode de paiement n'est pas encore disponible.", "warning")
        return redirect(url_for('panier.panier'))

    cart_items, total = Panier.get_panier(current_user.id)
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template("paiement.html", user=user_info, cart_items=cart_items, cart_total=total)

logger = logging.getLogger(__name__)

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
    """
    Étape 3 : Lancement du processus.
    On vérifie le panier et on lance le paiement Shwary SANS écrire dans la table commande.
    """
    phone = request.form.get("phone")
    if not validate_phone_drc(phone):
        flash("Numéro de téléphone invalide (Format attendu: +243...).", "danger")
        return redirect(url_for('panier.mobile_money'))

    normalized_phone = normalize_phone_drc(phone)
    cart_items, total = Panier.get_panier(current_user.id)
    
    if not cart_items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('panier.panier'))

    # Génération de la référence unique qui liera Shwary et notre future commande
    reference_id = str(uuid.uuid4())

    # --- NOUVEL ALGORITHME (ROBUSTE) ---
    # 1. Préparer les données de la commande AVANT d'appeler le paiement.
    user_info = current_user.get_claims()
    order_entries = []
    for item in cart_items:
        order_entries.append((
            item.get('id'), user_info.get('id'), user_info.get('first_name'), user_info.get('last_name'),
            user_info.get('adresse', 'Kinshasa, RDC'), item.get('product_id'), item.get('product_name'),
            item.get('product_price'), item.get('product_description'), item.get('product_image_url'),
            item.get('seller_id'), item.get('seller_name'), item.get('quantite'), item.get('prix_total'),
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "16:00", 2.5, 
            "en_attente_paiement",  # Statut initial
            reference_id
        ))

    try:
        # 2. Insérer la commande en BDD avec le statut "en_attente_paiement".
        Commande.create(order_entries)
        print(f"[INFO] Commande pré-enregistrée pour la référence {reference_id} avec le statut 'en_attente_paiement'.")
    except Exception as db_err:
        print(f"[DATABASE CRITICAL ERROR] Impossible de pré-enregistrer la commande : {db_err}")
        flash("Une erreur de base de données est survenue.", "danger")
        return redirect(url_for('panier.panier'))
    # --- FIN NOUVEL ALGORITHME ---
    
    try:
        print(f"\n[TRY] Initialisation du paiement Shwary pour l'utilisateur {current_user.id} (Montant: {total})...")
        
        # Construction de l'URL de callback sécurisée pour la production
        callback_url = Config.SHWARY_CALLBACK_URL.rstrip('/') + '/api/callback'
        if Config.CALLBACK_PATH_TOKEN:
            callback_url += f"/{Config.CALLBACK_PATH_TOKEN}"

        # Appel du nouveau service basé sur le SDK
        # Note: le service de paiement doit être mis à jour pour accepter `callback_url`
        payment_response = initiate_payment_sdk(normalized_phone, total, callback_url)
        
        shwary_transaction_id = payment_response.get('id')
        print(f"[SUCCESS] Requête de paiement acceptée par Shwary. ID Transaction: {shwary_transaction_id}")

        # On met à jour notre commande avec l'ID de transaction de Shwary pour faire le lien
        try:
            Commande.update_transaction_id(reference_id, shwary_transaction_id)
            print(f"[INFO] Commande {reference_id} liée à l'ID Shwary {shwary_transaction_id}.")
        except Exception as db_err:
            print(f"[DATABASE CRITICAL ERROR] Impossible de lier la commande à l'ID Shwary : {db_err}")
            flash("Une erreur de base de données est survenue après l'initiation du paiement.", "danger")
            return redirect(url_for('panier.panier'))
        return render_template('attente_paiement.html', reference_id=shwary_transaction_id)

    # Gestion des erreurs spécifiques au SDK pour un feedback utilisateur précis
    except ValidationError as e:
        # Erreur de validation (numéro, montant trop bas, etc.)
        print(f"[SDK VALIDATION ERROR] {e}")
        flash(f"Données de paiement invalides : {e}", "danger")
        return redirect(url_for('panier.mobile_money', method=request.args.get('method')))
    except AuthenticationError as e:
        # Mauvais credentials, problème côté back-office Shwary
        print(f"[SDK AUTH ERROR] {e}")
        current_app.logger.error(f"Erreur d'authentification Shwary: {e}")
        flash("Erreur de configuration du paiement. L'administrateur a été notifié.", "danger")
        return redirect(url_for('panier.panier'))
    except InsufficientFundsError:
        print("[SDK INSUFFICIENT FUNDS]")
        current_app.logger.error("Solde Shwary insuffisant.")
        flash("Le service de paiement est temporairement indisponible.", "danger")
        return redirect(url_for('panier.panier'))
    except RateLimitingError:
        print("[SDK RATE LIMITED]")
        flash("Le service de paiement est surchargé. Veuillez réessayer dans un instant.", "warning")
        return redirect(url_for('panier.panier'))
    except (ShwaryAPIError, ConnectionError, Exception) as e:
        # Erreur générale de l'API Shwary ou de connexion
        print(f"[SDK CRITICAL EXCEPTION] Échec lors de l'initialisation du paiement : {e}")
        current_app.logger.error(f"Erreur API Shwary ou connexion : {e}")
        flash("Une erreur technique est survenue lors de l'initialisation du paiement.", "danger")
        return redirect(url_for('panier.panier'))


@panier_bp.route("/api/check_status/<reference_id>")
@login_required
def check_status(reference_id):
    """
    Route pour le polling JS : vérifie l'état de la commande dans la BDD.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT etat FROM commande WHERE payment_intent_id = %s LIMIT 1", (reference_id,)) # reference_id ici est l'ID de transaction Shwary
        order = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if order:
            return jsonify({"status": order['etat']})
        
        return jsonify({"status": "not_found"}), 404
    except Exception as e:
        print(f"[ERROR] Échec lors du check_status de la référence {reference_id} : {e}")
        return jsonify({"status": "error"}), 500


@panier_bp.route("/paiement_finalise")
@login_required
def paiement_finalise():
    """Étape 4 : Affichage de la page de confirmation finale."""
    user_info = current_user.get_claims() if hasattr(current_user, 'get_claims') else {}
    return render_template('paiement confirmé.html', user=user_info)


@panier_bp.route('/api/callback', methods=['POST'])
@csrf.exempt
def shwary_callback_legacy():
    """Ancienne route de callback. Ne doit pas être utilisée en production si un token est configuré."""
    if Config.CALLBACK_PATH_TOKEN:
        current_app.logger.warning("Tentative d'accès au webhook non sécurisé alors qu'un token est configuré.")
        return jsonify({"error": "not found"}), 404
    return _handle_shwary_callback()

@panier_bp.route('/api/callback/<token>', methods=['POST'])
@csrf.exempt
def shwary_callback_secure(token):
    """Route de callback sécurisée par un token."""
    if not Config.CALLBACK_PATH_TOKEN or not secrets.compare_digest(token, Config.CALLBACK_PATH_TOKEN):
        return jsonify({"error": "not found"}), 404
    return _handle_shwary_callback()

def _handle_shwary_callback():
    """
    Logique de traitement du webhook, partagée par les deux routes.
    """
    data = request.get_json(silent=True)
    
    # Affichage clair du payload complet dans le terminal pour debug
    print("\n" + "="*50)
    print("[WEBHOOK RECEIVED] PAYLOAD REÇU DE SHWARY :")
    print(data)
    print("="*50 + "\n")

    # --- NOUVELLE LOGIQUE DE VÉRIFICATION SÉCURISÉE ---

    # 1. Vérifications de base
    if not data or str(data.get("userId")) != str(Config.SHWARY_MERCHANT_ID):
        print("[SECURITY ERROR] Le userId du payload ne correspond pas au MERCHANT_ID configuré ou payload vide.")
        return jsonify({"error": "Unauthorized"}), 401

    transaction_id = data.get("id")
    status = data.get("status")
    amount = data.get("amount")
    failure_reason = data.get("failureReason")

    if not all([transaction_id, status, amount]):
        return jsonify({"error": "Payload incomplet"}), 400

    # 2. Retrouver la commande dans notre BDD
    order = Commande.get_order_by_shwary_tx(transaction_id)
    if not order:
        print(f"[SECURITY WARNING] Commande introuvable pour la transaction Shwary {transaction_id}.")
        return jsonify({"error": "Order not found"}), 404

    # 3. Vérifier la cohérence du montant
    if int(float(order['prix_total'])) != int(float(amount)):
        print(f"[SECURITY ERROR] Montant incohérent. Attendu: {order['prix_total']}, Reçu: {amount}")
        return jsonify({"error": "Amount mismatch"}), 400

    # 4. Double confirmation : on interroge l'API de Shwary pour confirmer le statut
    try:
        if not verify_transaction_api(transaction_id, status, amount):
            print(f"[SECURITY CRITICAL] Le statut du webhook ({status}) n'a pas pu être confirmé via l'API pour la transaction {transaction_id}.")
            return jsonify({"error": "Transaction not confirmed"}), 400
    except Exception as api_err:
        print(f"[API_CONFIRM_ERROR] Impossible de re-vérifier la transaction {transaction_id} : {api_err}")
        return jsonify({"error": "Verification failed"}), 500

    # 2. Si le paiement a réussi ("completed" selon la documentation Shwary)
    if status == "completed":
        print(f"[TRY] Le paiement pour la transaction {transaction_id} a REUSSI (completed). Tentative d'écriture en BDD...")
        
        try:
            # 1. Mettre à jour le statut de la commande qui existe déjà
            updated_rows = Commande.update_status(transaction_id, "paye")
            
            if updated_rows == 0:
                print(f"[DATABASE WARNING] Aucune commande trouvée avec l'ID de transaction {transaction_id} à mettre à jour.")
                return jsonify({"status": "not_found"}), 200

            print(f"[DATABASE SUCCESS] Statut de la commande pour la transaction {transaction_id} mis à jour à 'paye'.")
            
            # 2. Retrouver l'ID de l'acheteur depuis la commande pour vider son panier
            buyer_id = Commande.get_buyer_id_from_ref(transaction_id)
            
            # 3. Nettoyage du panier de l'acheteur
            if buyer_id:
                Panier.clear_panier(buyer_id)
                print(f"[DATABASE SUCCESS] Panier de l'utilisateur {buyer_id} vidé.")
            else:
                print(f"[DATABASE WARNING] Impossible de retrouver l'acheteur pour la transaction {transaction_id} pour vider le panier.")
            
            # 4. Créer une notification de succès pour l'utilisateur
            if buyer_id:
                Notification.create(
                    user_id=buyer_id,
                    message=f"Votre paiement pour la commande (Réf: ...{transaction_id[-6:]}) a été accepté.",
                    type='success')
        except Exception as db_err:
            print(f"[DATABASE CRITICAL ERROR] Erreur lors de l'écriture de la commande en BDD : {db_err}")
            return jsonify({"error": "Database processing failed"}), 500

    # 3. Si le paiement a échoué ou a été annulé par le client
    elif status in ["failed", "cancelled"]:
        print(f"[PAYMENT FAILED/CANCELLED] Le paiement pour la transaction {transaction_id} a échoué. Statut Shwary: {status}.")
        print(f"[REASON] Raison de l'échec transmise par le terminal : '{failure_reason}'")

        try:
            # Mettre à jour le statut de la commande
            Commande.update_status(transaction_id, "echoue")
            print(f"[INFO] Statut de la commande pour la transaction {transaction_id} mis à jour à 'echoue'.")

            # Créer une notification d'échec pour l'utilisateur
            buyer_id = Commande.get_buyer_id_from_ref(transaction_id)
            if buyer_id:
                Notification.create(
                    user_id=buyer_id,
                    message=f"Votre paiement pour la commande (Réf: ...{transaction_id[-6:]}) a échoué.",
                    type='danger')
        except Exception as err: # noqa
            print(f"[ERROR] Impossible d'enregistrer l'échec en BDD : {err}")

    else:
        # Statuts intermédiaires (ex: 'submitted' ou 'pending') -> Shwary traite l'opération, on ne fait rien.
        print(f"[INFO] Statut intermédiaire reçu : '{status}'. On attend le résultat final.")

    # Réponse rapide à Shwary (Important: Timeout de 10s max exigé par Shwary)
    return jsonify({"status": "updated"}), 200


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
