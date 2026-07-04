import requests
from config import Config


def initiate_remote_payment(phone, amount):
    """
    Initie une demande de paiement en appelant le microservice externe.
    """
    # Construction de l'URL complète de l'endpoint
    url = f"{Config.PAYMENT_MICROSERVICE_URL.rstrip('/')}/api/payment/initiate"
    
    payload = {
        "phone": phone,
        "amount": float(amount),
        "country": "DRC"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Envoi de la requête POST au microservice
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    
    # Lève une exception si la requête a échoué (statut 4xx ou 5xx)
    response.raise_for_status()
    
    # Retourne la réponse JSON du microservice
    return response.json()