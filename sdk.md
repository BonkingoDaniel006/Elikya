import os
import logging
from flask import Flask, render_template, request, jsonify
from shwary import Shwary, ValidationError, AuthenticationError, ShwaryAPIError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialisation unique du client Shwary
shwary_client = Shwary(
    merchant_id="0e0ca537-1d67-414d-8f13-3238be68766e",
    merchant_key="shwary_d68f0f5d-e7d9-4fb6-ab1d-36f480d0ec9f",
    is_sandbox=False
)

@app.route('/')
def index():
    return render_template('formulaire.html')

@app.route('/api/payment/initiate', methods=["POST"])
def initiate_payment():
    """
    Initialise un paiement Shwary.
    Prend en charge le JSON ou le formulaire standard HTML.
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
            phone = data.get('phone')
            amount = data.get('amount')
            country = data.get('country', 'DRC')
        else:
            phone = request.form.get('phone') or request.form.get('number')
            amount = request.form.get('amount') or request.form.get('montant')
            country = request.form.get('country', 'DRC')

        if not phone or not amount:
            return jsonify({"error": "Missing phone or amount"}), 400
            
        # Appel de l'API Shwary
        payment = shwary_client.initiate_payment(
            country=country,
            amount=float(amount),
            phone_number=phone,
            callback_url="https://essaie-shwary-1.onrender.com/api/webhooks/shwary"
        )
        
        # CORRECTION ICI : Utilisation des attributs de l'objet (.id et .status)
        return jsonify({
            "success": True,
            "transaction_id": payment.id,
            "status": payment.status,
        }), 200
        
    except ValidationError as e:
        app.logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except AuthenticationError as e:
        app.logger.error(f"Auth error: {e}")
        return jsonify({"error": "Shwary authentication failed"}), 401
    except ShwaryAPIError as e:
        app.logger.error(f"API error: {e}")
        return jsonify({"error": f"Shwary error: {e.message}"}), e.status_code
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

@app.route("/api/webhooks/shwary", methods=["POST"])
def handle_shwary_webhook():
    """
    Reçoit les notifications asynchrones de Shwary (Webhooks).
    """
    try:
        data = request.get_json()
        transaction_id = data.get("id")
        status = data.get("status")

        app.logger.info(f"Received webhook: {transaction_id} -> {status}")

        if status == "completed":
            app.logger.info(f"Payment completed: {transaction_id}")
        elif status == "failed":
            app.logger.warning(f"Payment failed: {transaction_id}")

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.error(f"Webhook processing error: {e}")
        return jsonify({"status": "error"}), 500


@app.route("/api/transactions/<transaction_id>", methods=["GET"])
def get_transaction_status(transaction_id):
    """
    Récupère manuellement le statut d'une transaction Shwary.
    """
    try:
        tx = shwary_client.get_transaction(transaction_id)
        
        # CORRECTION ICI AUSSI : Utilisation de la notation par points
        return jsonify({
            "id": tx.id,
            "status": tx.status,
            "amount": tx.amount,
        }), 200
    except ShwaryAPIError as e:
        if e.status_code == 404:
            return jsonify({"error": "Transaction not found"}), 404
        
        app.logger.error(f"Error fetching transaction: {e}")
        return jsonify({"error": "Server error"}), 500
    

@app.route('/attente')
def attente_page():
    return render_template('attente.html')

@app.route('/resultat')
def resultat_page():
    return render_template('resultat.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)