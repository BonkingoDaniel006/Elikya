from shwary import (
    AuthenticationError,
    InsufficientFundsError,
    RateLimitingError,
    Shwary,
    ShwaryAPIError,
    ValidationError,
)

from config import Config

_client = None


def _ensure_credentials():
    """Vérifie la présence des identifiants Shwary dans la configuration."""
    if not Config.SHWARY_MERCHANT_ID or not Config.SHWARY_MERCHANT_KEY:
        raise ValueError("Les identifiants SHWARY_MERCHANT_ID et SHWARY_MERCHANT_KEY sont manquants dans la configuration.")


def get_shwary_client():
    """Initialise et retourne un client Shwary unique (singleton)."""
    global _client
    _ensure_credentials()
    if _client is None:
        _client = Shwary(
            merchant_id=Config.SHWARY_MERCHANT_ID,
            merchant_key=Config.SHWARY_MERCHANT_KEY,
            is_sandbox=Config.SHWARY_SANDBOX,
        )
    return _client


def create_payment(phone, amount):
    """
    Initie une demande de paiement via le SDK Shwary.
    Lève des exceptions spécifiques en cas d'erreur pour un meilleur contrôle.
    """
    client = get_shwary_client()
    # Le SDK utilise l'URL de callback configurée lors de l'initialisation si non fournie ici.
    # Pour plus de flexibilité, on la passe explicitement.
    payment = client.initiate_payment(
        country="DRC",
        amount=float(amount),
        phone_number=phone,
        callback_url=Config.SHWARY_CALLBACK_URL,
    )
    return payment.model_dump()


def verify_transaction_api(tx_id, expected_status, expected_amount):
    """
    Confirme le statut d'une transaction en interrogeant directement l'API Shwary.
    C'est une mesure de sécurité cruciale pour valider les webhooks.
    """
    client = get_shwary_client()
    tx = client.get_transaction(tx_id)

    # Vérification stricte du statut et du montant
    if tx.status != expected_status:
        return False
    if int(tx.amount) != int(expected_amount):
        return False

    return True