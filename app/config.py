import os
import json

# Railway/Render/Heroku: use DATABASE_URL para conexão
DB_URL = os.environ.get("DATABASE_URL")

# (Opcional) compatibilidade com DB_PARAMS/DB_PASSWORD
DB_PARAMS = json.loads(os.environ.get("DB_PARAMS", '{}'))
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Pontuação parametrizável por variáveis de ambiente
POINTS = {
    'MD1': int(os.environ.get('POINTS_MD1', 2)),
    'MD3_WINNER': int(os.environ.get('POINTS_MD3_WINNER', 1)),
    'MD3_SCORE': int(os.environ.get('POINTS_MD3_SCORE', 5)),
    'MD5_WINNER': int(os.environ.get('POINTS_MD5_WINNER', 1)),
    'MD5_SCORE': int(os.environ.get('POINTS_MD5_SCORE', 5))
}
