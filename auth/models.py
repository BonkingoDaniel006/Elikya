from flask_login import UserMixin
import mysql.connector
from mysql.connector import pooling
from config import Config

# Création d'un pool de connexions global
db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

class User(UserMixin):
    def __init__(self, id, email, password, prenom=None, nom_boutique=None):
        self.id = id
        self.email = email
        self.password = password
        self.prenom = prenom
        self.nom_boutique = nom_boutique

    @staticmethod
    def get_db_connection():
        return db_pool.get_connection()

    @classmethod
    def get_by_id(cls, user_id):
        conn = cls.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password, prenom, nom_boutique FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return cls(row['id'], row['email'], row['password'], row['prenom'], row['nom_boutique'])
        return None
    @classmethod
    def get_by_email(cls, email):
        conn = cls.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password, prenom, nom_boutique FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return cls(row['id'], row['email'], row['password'], row['prenom'], row['nom_boutique'])
        return None