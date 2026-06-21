from ext import get_db_connection
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
    def verifier_mot_de_passe(cls, user_id, password_a_tester, bcrypt_instance):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row and row['password']:
            # Utilise l'instance bcrypt passée pour valider le hash
            return bcrypt_instance.check_password_hash(row['password'], password_a_tester)
        return False
    
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

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
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
        except Exception as e:
            print(f"Erreur lors de la modification : {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    



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