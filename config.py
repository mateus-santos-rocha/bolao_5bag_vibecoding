# config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil'
    # Para começar, usaremos um banco de dados local (SQLite).
    # Quando for para produção, trocaremos esta linha pela URL do seu servidor SQL online.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///../instance/bolao.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
