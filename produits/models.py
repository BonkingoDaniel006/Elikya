from ext import db_session
import os
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from werkzeug.datastructures import FileStorage
import random


def calculer_prix_affiche(price):
    """Applique la commission de la plateforme au prix saisi par le vendeur."""
    cent = Decimal("0.01")
    try:
        prix_saisi = Decimal(str(price).replace(",", "."))
        if not prix_saisi.is_finite() or prix_saisi < 0:
            raise ValueError("Le prix doit être un nombre non négatif.")
        prix_saisi = prix_saisi.quantize(cent, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Le prix doit être un nombre positif valide.") from exc

    if prix_saisi < Decimal("1000"):
        return (prix_saisi + Decimal("20.00")).quantize(
            cent, rounding=ROUND_HALF_UP
        )

    return (prix_saisi * Decimal("1.02")).quantize(
        cent, rounding=ROUND_HALF_UP
    )


class Produits():
    def __init__(self, id, seller_id, name, price, description, image_url):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url

    @classmethod
    def search(cls, query):
        """Compatibilité : renvoie la première page de résultats."""
        produits, _ = cls.search_page(query)
        return produits

    @classmethod
    def search_page(cls, query, after_id=None, limit=24):
        """Recherche par curseur pour éviter de charger toute la table."""
        limit = max(1, min(int(limit), 50))
        search_query = f"%{query}%"
        sql = """
            SELECT p.id, p.seller_id, p.name, p.price, p.description,
                   p.image_url, p.categorie, u.nom_boutique
            FROM produits p
            JOIN users u ON p.seller_id = u.id
            WHERE (p.name LIKE %s OR p.description LIKE %s)
        """
        params = [search_query, search_query]
        if after_id is not None:
            sql += " AND p.id < %s"
            params.append(after_id)
        sql += " ORDER BY p.id DESC LIMIT %s"
        params.append(limit + 1)

        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(sql, tuple(params))
            produits = cursor.fetchall()
        has_more = len(produits) > limit
        produits = produits[:limit]
        next_cursor = produits[-1]["id"] if has_more else None
        return produits, next_cursor

class Details_produit():
    def __init__(self, id, seller_id, name, price, description, image_url, categorie, seller_name=None):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.seller_name = seller_name
        self.categorie = categorie



    def get_claims(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "seller_name": self.seller_name, 
            "categorie": self.categorie
        }
    @classmethod
    def get_by_id(cls, product_id):
        """Récupère les détails d'un produit par son ID"""
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute("""
                SELECT p.id, p.seller_id, p.name, p.price, p.description,
                       p.image_url, p.categorie,
                       u.nom_boutique AS seller_name
                FROM produits p 
                JOIN users u ON p.seller_id = u.id 
                WHERE p.id = %s
            """, (product_id,))
            row = cursor.fetchone()
            if row:
                return cls(
                    id=row['id'],
                    seller_id=row['seller_id'],
                    name=row['name'],
                    price=row['price'],
                    description=row['description'],
                    image_url=row['image_url'],
                    seller_name=row['seller_name'],
                    categorie=row['categorie']
                )
            return None


class Add_panier():
    def __init__(self, id, buyer_id, buyer_first_name, buyer_last_name, product_id, product_name, product_price, product_description, product_image_url, seller_id, seller_name, quantite, prix_total):
        self.id = id
        self.buyer_id = buyer_id
        self.buyer_first_name = buyer_first_name
        self.buyer_last_name = buyer_last_name
        self.product_id = product_id
        self.product_name = product_name
        self.product_price = product_price
        self.product_description = product_description
        self.product_image_url = product_image_url
        self.seller_id = seller_id
        self.seller_name = seller_name
        self.quantite = quantite
        self.prix_total = prix_total


    def get_claims(self):
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "buyer_first_name": self.buyer_first_name,
            "buyer_last_name": self.buyer_last_name,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_price": self.product_price,
            "product_description": self.product_description,
            "product_image_url": self.product_image_url,
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "quantite": self.quantite,
            "prix_total": self.prix_total
        }

    @classmethod
    def create(cls, buyer_id, buyer_first_name, buyer_last_name, product_id, product_name, 
               product_price, product_description, product_image_url, seller_id,
               seller_name, quantite, prix_total, categorie):
        """Insère un nouvel article dans le panier (table panier)"""
        with db_session() as (conn, cursor):
            cursor.execute("""
                INSERT INTO panier (
                    buyer_id, buyer_first_name, buyer_last_name,
                    product_id, product_name, product_price, product_description, product_image_url,
                    seller_id, seller_name, quantite, prix_total, categorie
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                buyer_id, buyer_first_name, buyer_last_name,
                product_id, product_name, product_price, product_description, product_image_url,
                seller_id, seller_name, quantite, prix_total, categorie
            ))
            conn.commit()

class Ajouter_produit():
    def __init__(self, id, seller_id, name, price, description, image_url, categorie):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.categorie = categorie

    def get_claims(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "categorie": self.categorie
        }
    @classmethod
    def ajouter(cls, id, seller_id, name, price, description, image_url: FileStorage, categorie):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        final_image_path = None
        
        if image_url and image_url.filename != "":
            extension = image_url.filename.rsplit('.', 1)[-1].lower()
            if '.' in image_url.filename and extension in ALLOWED_EXTENSIONS:
                unique_filename = str(uuid.uuid4()) + "." + extension
                image_path = os.path.join("static/uploads", unique_filename)
                image_url.save(image_path)
                final_image_path = "/" + image_path.replace("\\", "/")
            else:
                return "Format de fichier non autorisé", 400

        with db_session() as (conn, cursor):
            cursor.execute("""
                INSERT INTO produits (id, seller_id, name, price, description, image_url, categorie)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""", (id, seller_id, name, price, description, final_image_path, categorie))
            conn.commit()



class Suprimer_produit():
    def __init__(self, id, seller_id, name, price, description, image_url):
        self.id = id
        self.seller_id = seller_id
        self.name= name
        self.price= price
        self.description= description
        self.image_url= image_url

    def get_claims(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url
        }
    @classmethod
    def supprimer(cls, id):
        with db_session() as (conn, cursor):
            cursor.execute("DELETE FROM produits WHERE id = %s", (id,))
            conn.commit()


    

class Modifier_produit():
    def __init__(self, id, seller_id, name, price, description, image_url):

        self.id= id
        self.seller_id = seller_id
        self.name= name
        self.price = price
        self.description= description
        self.image_url= image_url

    def get_claims(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url
        }
    
    @classmethod
    def modifier(cls, id, seller_id, name, price, description, image_url, categorie):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        final_image_path = None
        
        # 1. Gestion de l'upload si un nouveau fichier est fourni
        if image_url and hasattr(image_url, 'filename') and image_url.filename != "":
            extension = image_url.filename.rsplit('.', 1)[-1].lower()
            if '.' in image_url.filename and extension in ALLOWED_EXTENSIONS:
                unique_filename = str(uuid.uuid4()) + "." + extension
                image_path = os.path.join("static/uploads", unique_filename)
                image_url.save(image_path)
                final_image_path = "/" + image_path.replace("\\", "/")
            else:
                return "Format de fichier non autorisé", 400

        with db_session() as (conn, cursor):
            if final_image_path:
                # Mise à jour incluant la nouvelle image
                cursor.execute("UPDATE produits SET seller_id = %s, name = %s, price = %s, description = %s, image_url = %s, categorie = %s WHERE id = %s",
                               (seller_id, name, price, description, final_image_path, categorie, id))
            else:
                # Mise à jour sans changer l'image existante
                cursor.execute("UPDATE produits SET seller_id = %s, name = %s, price = %s, description = %s, categorie = %s WHERE id = %s",
                               (seller_id, name, price, description, categorie, id))
            conn.commit()