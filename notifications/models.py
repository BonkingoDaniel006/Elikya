from ext import get_db_connection

class Notification():
    def __init__(self):
        pass
    def get_claims(self):
        pass
    @classmethod
    def get_notifications(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notifications WHERE user_id = %s", (user_id,))
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications