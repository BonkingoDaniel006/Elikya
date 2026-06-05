import os 
from dotenv import load_dotenv

load_dotenv()



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'une_cle_tres_secrete_et_longue_12345')

    MYSQL_HOST = os.environ.get('DB_HOST')
    MYSQL_USER = os.environ.get('DB_USER')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD')
    MYSQL_DB = os.environ.get('DB_NAME')
    MYSQL_CURSORCLASS = 'DictCursor'