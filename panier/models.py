import mysql.connector
from mysql.connector import pooling
from config import Config

db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

class Panier():
    def __init__(self, id, buyer_id, buyer_first_name, buyer_last_name, product_id, product_name, product_price, product_description, product_image_url, seller_id, seller_name, quantite, prix_total):
        self.id = id
        self.buyer_id=buyer_id
        self.buyer_last_name= buyer_last_name
        self.buyer_first_name=buyer_first_name
        self.product_id =product_id
        self.product_name = product_name
        self.product_price = product_price
        self.product_description = product_description
        self.product_image_url = product_image_url
        self.seller_id = seller_id
        self.seller_name = seller_name
        self.quantite = quantite
        self.prix_total = prix_total


    def get_claims(self):
        return{
            "id": self.id,
            "buyer_id": self.buyer_id,
            "buyer_last_name": self.buyer_last_name,
            "buyer_first_name": self.buyer_first_name,
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
    @staticmethod
    def get_db_connection():
        return db_pool.get_connection()
    
    @classmethod
    def get_panier(cls, user_id):
        conn = cls.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Suppression de ORDER BY created_at DESC au cas où la colonne n'existerait pas
            cursor.execute("SELECT * FROM panier2 WHERE buyer_id = %s", (user_id,))
            cart_items = cursor.fetchall()
            total = 0
            for item in cart_items:
                try:
                    # Remplacement de la virgule par un point et conversion sécurisée
                    total += float(str(item.get("prix_total", 0)).replace(',', '.'))
                except ValueError:
                    pass
        except Exception as e:
            cart_items, total = [], 0
            print(f"Erreur SQL profil_acheteur: {e}")
        cursor.close()
        conn.close()
        return cart_items, total
    



