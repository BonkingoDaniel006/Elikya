from ext import get_db_connection
from datetime import datetime

class Notification():
    @classmethod
    def create(cls, user_id, message, type='info', link=None):
        """Crée une nouvelle notification pour un utilisateur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO notifications (user_id, message, type, link, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (user_id, message, type, link, datetime.now()))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_notifications(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notifications WHERE user_id = %s", (user_id,))
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications