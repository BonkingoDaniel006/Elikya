from ext import get_db_connection
import random

class Produits():
    def __init__(self, id, seller_id, name, price, description, image_url):
        self.id = id
        self.seller_id = seller_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url

    @classmethod
    def get_by_id(cls):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, b.nom_boutique 
            FROM produits p 
            JOIN users b ON p.seller_id = b.id
            """)
        produits = cursor.fetchall()
        random.shuffle(produits)
        cursor.close()
        conn.close()
        return produits
    

    @classmethod
    def get_by_name(cls, name):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produits WHERE name = %s", (name,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    
    @classmethod
    def get_by_seller(cls, nom_boutique):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produits WHERE nom_boutique = %s", (nom_boutique,))
        resultat = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultat

    
