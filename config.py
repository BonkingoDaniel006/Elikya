import os 
from dotenv import load_dotenv

load_dotenv()



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'une_cle_tres_secrete_et_longue_12345')

<<<<<<< HEAD
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', 'Daniel12349')
    MYSQL_DB = os.environ.get('DB_NAME', 'elikya_db')
=======
    MYSQL_HOST = os.getenv('DB_HOST')
    MYSQL_USER = os.getenv('DB_USER')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD')
    MYSQL_DB = os.getenv('DB_NAME')
>>>>>>> 7c6e5b7f0d0b8a8f8e3497b34892a81ea7987f1d
    MYSQL_CURSORCLASS = 'DictCursor'