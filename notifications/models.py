from ext import db_session
from datetime import datetime
import json

class Notification():
    @classmethod
    def create(cls, user_id, type, title, content, data=None):
        """Crée une nouvelle notification pour un utilisateur."""
        query = """
            INSERT INTO notifications (user_id, type, title, content, data, is_read, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 0, %s, %s)
        """
        now = datetime.now()
        # Sérialiser le dictionnaire 'data' en chaîne JSON s'il existe
        data_json = json.dumps(data) if data else None
        with db_session() as (conn, cursor):
            cursor.execute(query, (user_id, type, title, content, data_json, now, now))
            conn.commit()

    @classmethod
    def get_for_user(cls, user_id):
        """Récupère toutes les notifications pour un utilisateur, triées par date."""
        query = "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(query, (user_id,))
            notifications = cursor.fetchall()
        return notifications

    @classmethod
    def mark_as_read(cls, notification_id, user_id):
        """Marque une notification comme lue."""
        query = """
            UPDATE notifications 
            SET is_read = 1, read_at = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
        """
        now = datetime.now()
        with db_session() as (conn, cursor):
            # On vérifie que la notif appartient bien à l'user pour la sécurité
            cursor.execute(query, (now, now, notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0 # Retourne True si une ligne a été modifiée

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Marque toutes les notifications non lues d'un utilisateur comme lues."""
        query = "UPDATE notifications SET is_read = 1, read_at = %s, updated_at = %s WHERE user_id = %s AND is_read = 0"
        now = datetime.now()
        with db_session() as (conn, cursor):
            cursor.execute(query, (now, now, user_id))
            conn.commit()

    @classmethod
    def delete(cls, notification_id, user_id):
        """Supprime une notification."""
        query = "DELETE FROM notifications WHERE id = %s AND user_id = %s"
        with db_session() as (conn, cursor):
            cursor.execute(query, (notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0 # Retourne True si une ligne a été supprimée