# Arquivo: data_utils.py
# Descrição: Funções utilitárias para manipulação de dados (carregar e salvar JSON).

import json
import os
from constants import DATA_DIR 

def ensure_data_dir(championship_id=None):
    """Garante que o diretório de dados exista, incluindo subdiretório do campeonato se fornecido."""
    path_to_ensure = DATA_DIR
    if championship_id:
        path_to_ensure = os.path.join(DATA_DIR, str(championship_id))
    
    if not os.path.exists(path_to_ensure):
        os.makedirs(path_to_ensure)

def get_data_path(base_filename, championship_id=None):
    """Constrói o caminho para um arquivo de dados, global ou específico do campeonato."""
    if championship_id:
        return os.path.join(DATA_DIR, str(championship_id), base_filename)
    return os.path.join(DATA_DIR, base_filename)

def load_data(base_filename, championship_id=None, default_data_factory=None):
    """Carrega dados de um arquivo JSON."""
    path = get_data_path(base_filename, championship_id)
    ensure_data_dir(championship_id) 
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data_factory() if callable(default_data_factory) else default_data_factory if default_data_factory is not None else {}

def save_data(base_filename, data, championship_id=None):
    """Salva dados em um arquivo JSON."""
    path = get_data_path(base_filename, championship_id)
    ensure_data_dir(championship_id) 
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)