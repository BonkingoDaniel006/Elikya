from flask_login import UserMixin
from ext import get_db_connection

class User(UserMixin):
    def __init__(self, id, email, password, prenom=None, nom=None, postnom=None, description=None, profil=None, adresse=None, nom_boutique=None):
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # CORRECTION : On sélectionne toutes les colonnes nécessaires pour le header
        cursor.execute(
            "SELECT id, email, password, prenom, nom, postnom, description, profil, adresse, nom_boutique FROM users WHERE id = %s", 
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return cls(**row)
        return None
    @classmethod
    def get_by_email(cls, email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # CORRECTION : On sélectionne toutes les colonnes nécessaires pour le header
        cursor.execute(
            "SELECT id, email, password, prenom, nom, postnom, description, profil, adresse, nom_boutique FROM users WHERE email = %s", 
            (email,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return cls(**row)
        return None

    @classmethod
    def create_user(cls, data, hashed_password):
        """Insère un nouvel utilisateur en base de données après validation OTP."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO users (prenom, nom, postnom, email, naissance, password, description, adresse, nom_boutique)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['prenom'], data['nom'], data['postnom'], data['email'],
            data['naissance'], hashed_password, data['description'],
            data['adresse'], data['nom_boutique']
        )
        try:
            cursor.execute(query, values)
            conn.commit()
        finally:
            cursor.close()
            conn.close()