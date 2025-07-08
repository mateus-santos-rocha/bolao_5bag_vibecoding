import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, 'database_connection_parameters.json'), 'r') as f:
    DB_PARAMS = json.load(f)
with open(os.path.join(BASE_DIR, 'database_password.txt'), 'r') as f:
    DB_PASSWORD = f.read().strip()

# Pontuação parametrizável
POINTS = {
    'MD1': 2,
    'MD3_WINNER': 1,
    'MD3_SCORE': 5,
    'MD5_WINNER': 1,
    'MD5_SCORE': 5
}
