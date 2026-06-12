import os
import time
from flask import current_app
from werkzeug.utils import secure_filename
from ext import get_db_connection
from types import SimpleNamespace

class Ajouter_produit:
    @classmethod
    def ajouter(cls, id, seller_id, name, price, description, image_url):
        """
        image_url ici est l'objet FileStorage envoyé par le formulaire.
        """
        if not image_url or image_url.filename == '':
            return ("Veuillez sélectionner une image valide.", 400)

        # 1. Sécuriser le nom du fichier pour éviter les injections de chemin
        filename = secure_filename(image_url.filename)
        # Ajouter un timestamp pour éviter les collisions de noms de fichiers
        unique_filename = f"{int(time.time())}_{filename}"
        
        # 2. Définir le chemin physique complet sur le serveur
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            # 3. Sauvegarder réellement le fichier sur le disque dur du serveur
            image_url.save(file_path)
        except Exception as e:
            return (f"Erreur lors de l'enregistrement physique : {str(e)}", 500)

        # 4. Chemin relatif à enregistrer en BDD (pour être utilisé par url_for('static', ...))
        db_image_path = f"uploads/{unique_filename}"

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO products (seller_id, name, price, description, image_url) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (seller_id, name, price, description, db_image_path))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            # Supprimer le fichier si l'insertion en BDD échoue pour ne pas polluer le serveur
            if os.path.exists(file_path):
                os.remove(file_path)
            return (f"Erreur base de données : {str(e)}", 500)
        finally:
            cursor.close()
            conn.close()

class Details_produit:
    @classmethod
    def get_by_id(cls, product_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute("""
                SELECT p.*, u.nom_boutique as seller_name 
                FROM products p 
                JOIN users u ON p.seller_id = u.id 
                WHERE p.id = %s
            """, (product_id,))
            res = cursor.fetchone()
            return SimpleNamespace(**res) if res else None
        except Exception as e:
            print(f"Erreur lors de la récupération du produit: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

class Add_panier:
    @classmethod
    def create(cls, **kwargs):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cols = ", ".join(kwargs.keys())
            vals = [kwargs[k] for k in kwargs]
            placeholders = ", ".join(["%s"] * len(vals))
            cursor.execute(f"INSERT INTO panier2 ({cols}) VALUES ({placeholders})", vals)
            conn.commit()
        finally:
            cursor.close()
            conn.close()