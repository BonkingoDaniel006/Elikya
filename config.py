import os 


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'une_cle_tres_secrete_et_longue_12345')

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Daniel12349'
    MYSQL_DB = 'elikya_db'
    MYSQL_CURSORCLASS = 'DictCursor'