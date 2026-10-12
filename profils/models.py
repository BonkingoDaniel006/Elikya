from ext import db_session
from panier.models import Panier
import os
import uuid
from werkzeug.datastructures import FileStorage

class Buyer():
    def __init__(self, email, id, prenom, nom, postnom, description, profil, adresse):
        self.email = email
        self.id = id
        self.prenom = prenom
        self.nom = nom 
        self.postnom = postnom
        self.description = description
        self.profil = profil
        self.adresse = adresse

    def get_claims(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "postnom": self.postnom,
            "email": self.email,
            "description": self.description,
            "profil": self.profil,
            "adresse": self.adresse

        }
    @classmethod
    def get_by_id(cls, user_id):
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(
                "SELECT id, prenom, nom, postnom, email, description, profil, adresse FROM users WHERE id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
        if row:
            return cls(
                email=row['email'],
                id=row['id'],
                prenom=row['prenom'],
                nom=row['nom'],
                postnom=row['postnom'],
                description=row['description'],
                profil=row['profil'],
                adresse=row['adresse']
            )
        return None
    

    @classmethod
    def verifier_mot_de_passe(cls, user_id, password_a_tester, bcrypt_instance):
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
        
        if row and row['password']:
            # Utilise l'instance bcrypt passée pour valider le hash
            return bcrypt_instance.check_password_hash(row['password'], password_a_tester)
        return False
    
    @classmethod
    def get_panier(cls, user_id):
        cart_items, total, _ = Panier.get_panier_page(user_id)
        return cart_items, total

    @classmethod
    def get_panier_page(cls, user_id, after_id=None, limit=25):
        return Panier.get_panier_page(user_id, after_id=after_id, limit=limit)
    
    @classmethod
    def modifier(cls, id, prenom, nom, postnom, profil, adresse, hashed_new_password=None):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        final_image_path = None
        
        # 1. Gestion de l'upload d'image
        if profil and hasattr(profil, 'filename') and profil.filename != "":
            extension = profil.filename.rsplit('.', 1)[-1].lower()
            if '.' in profil.filename and extension in ALLOWED_EXTENSIONS:
                unique_filename = str(uuid.uuid4()) + "." + extension
                image_path = os.path.join("static/uploads", unique_filename)
                
                # S'assurer que le dossier static/uploads existe
                os.makedirs("static/uploads", exist_ok=True)
                
                profil.save(image_path)
                final_image_path = "/" + image_path.replace("\\", "/")
            else:
                return False

        with db_session() as (conn, cursor):
            # Construction dynamique de la requête SQL selon les données fournies
            query = "UPDATE users SET prenom = %s, nom = %s, postnom = %s, adresse = %s"
            params = [prenom, nom, postnom, adresse]

            if final_image_path:
                query += ", profil = %s"
                params.append(final_image_path)
                
            if hashed_new_password:
                query += ", password = %s"
                params.append(hashed_new_password)

            query += " WHERE id = %s"
            params.append(id)

            cursor.execute(query, tuple(params))
            conn.commit()
        return True
    



class Seller ():
    def __init__(self, id, prenom, nom, postnom, email, naissance, description, profil, adresse, nom_boutique):
        self.id = id
        self.prenom = prenom
        self.nom = nom
        self.postnom = postnom
        self.email = email
        self.naissance = naissance
        self.description = description
        self.profil = profil
        self.adresse = adresse
        self.nom_boutique = nom_boutique

    def get_claims(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "postnom": self.postnom,
            "email": self.email,
            "naissance": self.naissance,
            "description":self.description,
            "profil": self.profil,
            "adresse": self.adresse,
            "nom_boutique": self.nom_boutique
        }

    @classmethod
    def get_by_id(cls, user_id):
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(
                "SELECT id, prenom, nom, postnom, email, naissance, description, profil, adresse, nom_boutique FROM users WHERE id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
        if row:
            return cls(
                id=row['id'],
                prenom=row['prenom'],
                nom=row['nom'],
                postnom=row['postnom'],
                email=row['email'],
                naissance=row['naissance'],
                description=row['description'],
                profil=row['profil'],
                adresse=row['adresse'],
                nom_boutique=row['nom_boutique']
            )
        return None
    @classmethod
    def get_produits(cls, user_id):
        produits, _ = cls.get_produits_page(user_id)
        return produits

    @classmethod
    def get_produits_page(cls, user_id, after_id=None, limit=25):
        limit = max(1, min(int(limit), 50))
        query = """
            SELECT id, seller_id, name, price, description, image_url, categorie
            FROM produits WHERE seller_id = %s
        """
        params = [user_id]
        if after_id is not None:
            query += " AND id < %s"
            params.append(after_id)
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit + 1)

        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(query, tuple(params))
            produits = cursor.fetchall()
        has_more = len(produits) > limit
        produits = produits[:limit]
        next_cursor = produits[-1]["id"] if has_more else None
        return produits, next_cursor
    
    @classmethod
    def get_commandes(cls, user_id):
        commandes, _ = cls.get_commandes_page(user_id)
        return commandes

    @classmethod
    def get_commandes_page(cls, user_id, after_id=None, limit=25):
        limit = max(1, min(int(limit), 50))
        query = """
            SELECT id, seller_id, buyer_first_name, buyer_last_name,
                   date_creation, prix_total, etat, product_name,
                   quantite, product_price, product_image_url
            FROM commande WHERE seller_id = %s
        """
        params = [user_id]
        if after_id is not None:
            query += " AND id < %s"
            params.append(after_id)
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit + 1)

        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(query, tuple(params))
            commandes = cursor.fetchall()
        has_more = len(commandes) > limit
        commandes = commandes[:limit]
        next_cursor = commandes[-1]["id"] if has_more else None
        return commandes, next_cursor
    
    @classmethod
    def get_for_user(cls, user_id):
        """Récupère la première page de notifications pour compatibilité."""
        notifications, _ = cls.get_for_user_page(user_id)
        return notifications

    @classmethod
    def get_for_user_page(cls, user_id, after_id=None, limit=25):
        limit = max(1, min(int(limit), 50))
        query = """
            SELECT id, user_id, type, title, content, is_read, created_at
            FROM notifications WHERE user_id = %s
        """
        params = [user_id]
        if after_id is not None:
            query += " AND id < %s"
            params.append(after_id)
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit + 1)

        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(query, tuple(params))
            notifications = cursor.fetchall()
        has_more = len(notifications) > limit
        notifications = notifications[:limit]
        next_cursor = notifications[-1]["id"] if has_more else None
        return notifications, next_cursor
