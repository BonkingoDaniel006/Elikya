import hashlib

from flask import request, session
from flask_login import current_user
from flask_limiter.util import get_remote_address


def account_rate_limit_key():
    """Limite par identifiant sans conserver d'adresse email brute dans Redis."""
    identity = None
    if current_user.is_authenticated:
        identity = f"user:{current_user.get_id()}"
    else:
        identity = request.form.get('email')
        for session_key in ('pending_user', 'registration_step1_data'):
            data = session.get(session_key)
            if not identity and isinstance(data, dict):
                identity = data.get('email')

    if not identity:
        return f"ip:{get_remote_address()}"

    digest = hashlib.sha256(identity.strip().lower().encode('utf-8')).hexdigest()
    return f"account:{digest}"
