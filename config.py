import os

class Config:
# Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sanamed'

    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://usuario:sanamed@localhost/postsanamed'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de correo
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'sanamed467@gmail.com'
    MAIL_PASSWORD = 'bkca lkuj cahk rnlm'