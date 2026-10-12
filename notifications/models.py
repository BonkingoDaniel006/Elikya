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
        """Récupère la première page de notifications pour compatibilité."""
        notifications, _ = cls.get_for_user_page(user_id)
        return notifications

    @classmethod
    def get_for_user_page(cls, user_id, after_id=None, limit=25):
        limit = max(1, min(int(limit), 50))
        query = """
            SELECT id, user_id, type, title, content, data, is_read, created_at
            FROM notifications WHERE user_id = %s
        """
        params = [user_id]
        if after_id is not None:
            query += " AND id < %s"
            params.append(after_id)
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit + 1)

        with db_session(dictionary=True) as (_, cursor):
            cursor.execute(query, tuple(params))
            notifications = cursor.fetchall()
        has_more = len(notifications) > limit
        notifications = notifications[:limit]
        next_cursor = notifications[-1]["id"] if has_more else None
        return notifications, next_cursor

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