import os 


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'une_cle_tres_secrete_et_longue_12345')

    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', 'Daniel12349')
    MYSQL_DB = os.environ.get('DB_NAME', 'elikya_db')
    MYSQL_CURSORCLASS = 'DictCursor'