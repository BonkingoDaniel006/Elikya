from ext import get_db_connection

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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, prenom, nom, postnom, email, description, profil, adresse FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produits WHERE seller_id = %s", (user_id,))
        produits = cursor.fetchall()
        cursor.close()
        conn.close()
        return produits