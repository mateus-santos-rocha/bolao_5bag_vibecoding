# Arquivo: constants.py
# Descrição: Armazena constantes e configurações padrão do aplicativo.

import hashlib
import os

DATA_DIR = "bolao_data" 

# Nomes base para arquivos globais (CORRIGIDO)
USERS_BASENAME = "users.json"
CHAMPIONSHIPS_BASENAME = "championships.json"
APP_CONFIG_BASENAME = "app_config.json"

# Nomes base para arquivos específicos de campeonatos (já estavam corretos)
TEAMS_BASENAME = "teams.json"
MATCHES_BASENAME = "matches.json"
BETS_BASENAME = "bets.json"
CHAMPIONSHIP_SETTINGS_BASENAME = "championship_settings.json" 
LATE_BET_REQUESTS_BASENAME = "late_bet_requests.json"

DEFAULT_ADMIN_PASSWORD = "admin123"

def hash_password_constants(password):
    return hashlib.sha256(password.encode()).hexdigest()

DEFAULT_APP_CONFIG = {
    "admin_password_hash": hash_password_constants(DEFAULT_ADMIN_PASSWORD)
}

DEFAULT_CHAMPIONSHIP_SETTINGS = {
    "points_md1": 2,
    "points_md3_md5_winner": 1,
    "points_md3_md5_score": 5
}

# --- FIM DO ARQUIVO: constants.py ---