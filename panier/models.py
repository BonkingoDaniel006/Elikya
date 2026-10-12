from ext import db_session

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
    @classmethod
    def get_panier(cls, user_id):
        cart_items, total, _ = cls.get_panier_page(user_id)
        return cart_items, total

    @classmethod
    def get_panier_page(cls, user_id, after_id=None, limit=25):
        limit = max(1, min(int(limit), 50))
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(
                "SELECT COALESCE(SUM(prix_total), 0) AS total FROM panier WHERE buyer_id = %s",
                (user_id,)
            )
            total_row = cursor.fetchone()
            query = """
                SELECT id, buyer_id, buyer_first_name, buyer_last_name,
                       product_id, product_name, product_price,
                       product_description, product_image_url, seller_id,
                       seller_name, quantite, prix_total
                FROM panier WHERE buyer_id = %s
            """
            params = [user_id]
            if after_id is not None:
                query += " AND id < %s"
                params.append(after_id)
            query += " ORDER BY id DESC LIMIT %s"
            params.append(limit + 1)
            cursor.execute(query, tuple(params))
            cart_items = cursor.fetchall()

        has_more = len(cart_items) > limit
        cart_items = cart_items[:limit]
        next_cursor = cart_items[-1]["id"] if has_more else None
        total = float(total_row["total"]) if total_row and total_row["total"] else 0
        return cart_items, total, next_cursor

    @classmethod
    def clear_panier(cls, user_id):
        with db_session() as (conn, cursor):
            cursor.execute("DELETE FROM panier WHERE buyer_id = %s", (user_id,))
            conn.commit()

class Commande:
    @classmethod
    def create(cls, data_list):
        with db_session() as (conn, cursor):
            cursor.executemany("""
                INSERT INTO commande (panier_id, buyer_id, buyer_first_name, buyer_last_name, adresse, product_id, product_name, product_price, product_description, product_image_url, seller_id, seller_name, quantite, prix_total, date_reception, date_livraison, heure_livraison, frais_livraison, etat)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, data_list)
            conn.commit()


class Suprimer_panier():
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
    @classmethod
    def supprimer(cls, id, buyer_id):
        with db_session() as (conn, cursor):
            cursor.execute("DELETE FROM panier WHERE id = %s AND buyer_id = %s", (id, buyer_id))
            conn.commit()




class Modifier_panier():
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
    
    @classmethod
    def modifier(cls, id, buyer_id, quantite, prix_total):
        with db_session() as (conn, cursor):
            cursor.execute("""
                UPDATE panier 
                SET quantite = %s, prix_total = %s 
                WHERE id = %s AND buyer_id = %s
            """, (quantite, prix_total, id, buyer_id))
            conn.commit()
