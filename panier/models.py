from ext import get_db_connection

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Suppression de ORDER BY created_at DESC au cas où la colonne n'existerait pas
            cursor.execute("SELECT * FROM panier WHERE buyer_id = %s", (user_id,))
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

    @classmethod
    def clear_panier(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM panier WHERE buyer_id = %s", (user_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

class Commande:
    @classmethod
    def create(cls, data_list):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany("""
                INSERT INTO commande (
                    panier_id, buyer_id, buyer_first_name, buyer_last_name, adresse,
                    product_id, product_name, product_price, product_description, product_image_url,
                    seller_id, seller_name, quantite, prix_total, date_reception, date_livraison, heure_livraison,
                    frais_livraison, etat, payment_intent_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, data_list)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def update_transaction_id(cls, internal_ref, shwary_tx_id):
        """Met à jour la commande avec l'ID de transaction de Shwary."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE commande SET payment_intent_id = %s WHERE payment_intent_id = %s", (shwary_tx_id, internal_ref))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def update_status(cls, reference_id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE commande SET etat = %s WHERE payment_intent_id = %s", (status, reference_id))
            conn.commit()
            return cursor.rowcount # Renvoie le nombre de lignes affectées (0 ou plus)
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_buyer_id_from_ref(cls, reference_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT buyer_id FROM commande WHERE payment_intent_id = %s LIMIT 1", (reference_id,))
            result = cursor.fetchone()
            return result['buyer_id'] if result else None
        finally:
            cursor.close()
            conn.close()



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
    def supprimer(cls, id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM panier WHERE id = %s", (id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()




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
    def modifier(cls, id, quantite, prix_total):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE panier 
                SET quantite = %s, prix_total = %s 
                WHERE id = %s
            """, (quantite, prix_total, id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_order_by_shwary_tx(cls, shwary_tx_id):
        """Récupère une commande via son ID de transaction Shwary."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM commande WHERE payment_intent_id = %s", (shwary_tx_id,))
            return cursor.fetchone() # Récupère le résultat de la requête précédente
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def record_webhook_event(cls, event_key, shwary_tx_id, status):
        """Enregistre un événement de webhook pour éviter les doublons."""
        # Note: Pour une application de production, cette table devrait exister.
        # CREATE TABLE webhook_events (event_key VARCHAR(255) PRIMARY KEY, ...);
        # Pour cet exercice, nous allons simuler en loggant.
        # Dans un cas réel, on ferait un INSERT IGNORE ici.
        print(f"[WEBHOOK_EVENT] Enregistrement de l'événement: {event_key}")
        return True
