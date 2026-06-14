from ext import get_db_connection
import os
import uuid
from werkzeug.datastructures import FileStorage


class Details_produit():
    def __init__(self, id, seller_id, name, price, description, image_url, seller_name=None):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.seller_name = seller_name

    def get_claims(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "seller_name": self.seller_name
        }
    @classmethod
    def get_by_id(cls, product_id):
        """Récupère les détails d'un produit par son ID"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT p.*, u.nom_boutique AS seller_name 
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
                    seller_name=row['seller_name']
                )
            return None
        finally:
            cursor.close()
            conn.close()


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
               seller_name, quantite, prix_total):
        """Insère un nouvel article dans le panier (table panier)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO panier (
                    buyer_id, buyer_first_name, buyer_last_name,
                    product_id, product_name, product_price, product_description, product_image_url,
                    seller_id, seller_name, quantite, prix_total
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                buyer_id, buyer_first_name, buyer_last_name,
                product_id, product_name, product_price, product_description, product_image_url,
                seller_id, seller_name, quantite, prix_total
            ))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

class Ajouter_produit():
    def __init__(self, id, seller_id, name, price, description, image_url):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url

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
    def ajouter(cls, id, seller_id, name, price, description, image_url: FileStorage):
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

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO produits (id, seller_id, name, price, description, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)""", (id, seller_id, name, price, description, final_image_path))
            conn.commit()
        finally:
            cursor.close()
            conn.close()



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
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM produits WHERE id = %s", (id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


    