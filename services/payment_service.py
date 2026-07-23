import requests
from config import Config
from flask import current_app # Importer current_app pour accéder au logger


def initiate_remote_payment(phone, amount):
    """
    Initie une demande de paiement en appelant le microservice externe.
    """
    # Construction de l'URL complète de l'endpoint
    if not Config.PAYMENT_MICROSERVICE_URL:
        current_app.logger.critical("FATAL: PAYMENT_MICROSERVICE_URL n'est pas configuré !")
        raise ValueError("L'URL du service de paiement n'est pas configurée.")

    url = f"{Config.PAYMENT_MICROSERVICE_URL.rstrip('/')}/api/payment/initiate"
    
    payload = {
        "phone": phone,
        "amount": float(amount),
        "country": "DRC"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    current_app.logger.info(f"Tentative d'initiation de paiement vers : {url}")
    try:
        # Envoi de la requête POST au microservice
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
        response.raise_for_status()
        
        # Retourne la réponse JSON du microservice
        return response.json()
    except requests.exceptions.RequestException as e:
        # Capture toutes les erreurs liées au réseau (connexion, timeout, etc.)
        current_app.logger.error(f"Erreur réseau en contactant le service de paiement : {e}")
        raise  # Relance l'exception pour que la route puisse la gérer
    except Exception as e:
        current_app.logger.error(f"Erreur inattendue lors de l'appel au service de paiement : {e}")
        raise