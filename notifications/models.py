from ext import get_db_connection
from datetime import datetime
import json

class Notification():
    @classmethod
    def create(cls, user_id, type, title, content, data=None):
        """Crée une nouvelle notification pour un utilisateur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO notifications (user_id, type, title, content, data, is_read, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 0, %s, %s)
        """
        now = datetime.now()
        # Sérialiser le dictionnaire 'data' en chaîne JSON s'il existe
        data_json = json.dumps(data) if data else None
        try:
            cursor.execute(query, (user_id, type, title, content, data_json, now, now))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_for_user(cls, user_id):
        """Récupère toutes les notifications pour un utilisateur, triées par date."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications

    @classmethod
    def mark_as_read(cls, notification_id, user_id):
        """Marque une notification comme lue."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            UPDATE notifications 
            SET is_read = 1, read_at = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
        """
        now = datetime.now()
        try:
            # On vérifie que la notif appartient bien à l'user pour la sécurité
            cursor.execute(query, (now, now, notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0 # Retourne True si une ligne a été modifiée
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Marque toutes les notifications non lues d'un utilisateur comme lues."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE notifications SET is_read = 1, read_at = %s, updated_at = %s WHERE user_id = %s AND is_read = 0"
        now = datetime.now()
        try:
            cursor.execute(query, (now, now, user_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def delete(cls, notification_id, user_id):
        """Supprime une notification."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "DELETE FROM notifications WHERE id = %s AND user_id = %s"
        try:
            cursor.execute(query, (notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0 # Retourne True si une ligne a été supprimée
        finally:
            cursor.close()
            conn.close()