import json
import logging

from flask import current_app, has_app_context
from flask_login import UserMixin
from redis.exceptions import RedisError

from ext import db_session, get_redis_client

logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, email, password=None, prenom=None, nom=None, postnom=None, description=None, profil=None, adresse=None, nom_boutique=None):
        self.id = id
        self.email = email
        self.password = password
        self.prenom = prenom
        self.nom = nom
        self.postnom = postnom
        self.description = description
        self.profil = profil
        self.adresse = adresse
        self.nom_boutique = nom_boutique

    def get_claims(self):
        """Returns user information as a dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.prenom,
            "last_name": self.nom,
            "postnom": self.postnom,
            "description": self.description,
            "profil": self.profil,
            "adresse": self.adresse,
            "nom_boutique": self.nom_boutique
        }

    @classmethod
    def get_by_id(cls, user_id):
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(
                "SELECT id, email, password, prenom, nom, postnom, description, profil, adresse, nom_boutique FROM users WHERE id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
        if row:
            return cls(**row)
        return None

    @classmethod
    def get_cached_by_id(cls, user_id):
        cache = get_redis_client()
        cache_key = f"user:{user_id}"
        if cache is not None:
            try:
                cached = cache.get(cache_key)
            except RedisError:
                logger.warning("Redis indisponible pour le cache utilisateur.")
            else:
                if cached:
                    try:
                        return cls(**json.loads(cached))
                    except (TypeError, ValueError):
                        logger.warning("Entrée invalide dans le cache utilisateur %s.", user_id)
                        try:
                            cache.delete(cache_key)
                        except RedisError:
                            logger.warning("Impossible de supprimer une entrée Redis invalide.")

        user = cls.get_by_id(user_id)
        if user is None or cache is None:
            return user

        user_data = {
            "id": user.id,
            "email": user.email,
            "prenom": user.prenom,
            "nom": user.nom,
            "postnom": user.postnom,
            "description": user.description,
            "profil": user.profil,
            "adresse": user.adresse,
            "nom_boutique": user.nom_boutique,
        }
        ttl = current_app.config.get("USER_CACHE_TTL", 60) if has_app_context() else 60
        try:
            cache.setex(cache_key, ttl, json.dumps(user_data))
        except RedisError:
            logger.warning("Impossible d'écrire l'utilisateur %s dans le cache Redis.", user_id)
        return user

    @classmethod
    def invalidate_cache(cls, user_id):
        cache = get_redis_client()
        if cache is None:
            return
        try:
            cache.delete(f"user:{user_id}")
        except RedisError:
            logger.warning("Impossible d'invalider le cache utilisateur %s.", user_id)

    @classmethod
    def get_by_email(cls, email):
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(
                "SELECT id, email, password, prenom, nom, postnom, description, profil, adresse, nom_boutique FROM users WHERE email = %s",
                (email,)
            )
            row = cursor.fetchone()
        if row:
            return cls(**row)
        return None

    @classmethod
    def create_user(cls, data, hashed_password):
        """Insère un nouvel utilisateur en base de données après validation OTP."""
        query = """
            INSERT INTO users (prenom, nom, postnom, email, naissance, password, description, adresse, nom_boutique)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['prenom'], data['nom'], data['postnom'], data['email'],
            data['naissance'], hashed_password, data['description'],
            data['adresse'], data['nom_boutique']
        )
        with db_session() as (conn, cursor):
            cursor.execute(query, values)
            conn.commit()