import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict
import hashlib # Para senhas, embora aqui seja um exemplo simples

# --- Configuration & Constants ---
DATA_DIR = "bolao_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TEAMS_FILE = os.path.join(DATA_DIR, "teams.json")
MATCHES_FILE = os.path.join(DATA_DIR, "matches.json")
BETS_FILE = os.path.join(DATA_DIR, "bets.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Senha padrão do admin (deve ser alterada)
# Em um app real, use um hash seguro e salt.
DEFAULT_ADMIN_PASSWORD = "admin123"
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

DEFAULT_SETTINGS = {
    "points_md1": 2,
    "points_md3_md5_winner": 1,
    "points_md3_md5_score": 5,
    "admin_password_hash": hash_password(DEFAULT_ADMIN_PASSWORD)
}

# --- Helper Functions for Data Handling ---
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_data(file_path, default_data_factory=None):
    ensure_data_dir()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data_factory() if callable(default_data_factory) else default_data_factory if default_data_factory is not None else {}

def save_data(file_path, data):
    ensure_data_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Initialize Session State ---
def initialize_session_state():
    # Estado de Login
    if 'logged_in_user' not in st.session_state:
        st.session_state.logged_in_user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'page' not in st.session_state:
        st.session_state.page = "Login"

    # Carregar dados para o estado da sessão (apenas uma vez)
    if 'settings' not in st.session_state:
        st.session_state.settings = load_data(SETTINGS_FILE, lambda: DEFAULT_SETTINGS)
        if not os.path.exists(SETTINGS_FILE) or not load_data(SETTINGS_FILE): # Garante que as configurações padrão sejam salvas se o arquivo não existir
            save_data(SETTINGS_FILE, st.session_state.settings)
            
    if 'users' not in st.session_state:
        # Garante que o usuário admin exista com a senha padrão (ou a do arquivo)
        users_data = load_data(USERS_FILE, lambda: {})
        if "admin" not in users_data:
            users_data["admin"] = {"password_hash": st.session_state.settings.get("admin_password_hash", hash_password(DEFAULT_ADMIN_PASSWORD)), "is_admin": True}
        elif "password_hash" not in users_data["admin"]: # Garante que o admin tenha um hash de senha
             users_data["admin"]["password_hash"] = st.session_state.settings.get("admin_password_hash", hash_password(DEFAULT_ADMIN_PASSWORD))
        st.session_state.users = users_data
        save_data(USERS_FILE, st.session_state.users)


    if 'teams' not in st.session_state:
        st.session_state.teams = load_data(TEAMS_FILE, lambda: [])
    if 'matches' not in st.session_state:
        st.session_state.matches = load_data(MATCHES_FILE, lambda: [])
    if 'bets' not in st.session_state:
        st.session_state.bets = load_data(BETS_FILE, lambda: [])

# --- Authentication Functions ---
def login_page():
    st.header("Login - Bolão do Mundial de LoL 5BAG")
    
    with st.form("login_form"):
        username = st.text_input("Nome de Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Login")

        if submitted:
            users = st.session_state.users
            if username in users:
                user_data = users[username]
                # Para admin, checa a senha. Para jogadores, o nome de usuário é suficiente nesta versão simplificada.
                if user_data.get("is_admin", False):
                    if user_data.get("password_hash") == hash_password(password):
                        st.session_state.logged_in_user = username
                        st.session_state.is_admin = True
                        st.session_state.page = "Dashboard Admin"
                        st.rerun()
                    else:
                        st.error("Senha de admin incorreta.")
                else: # Login de jogador (sem senha obrigatória para simplificar)
                    st.session_state.logged_in_user = username
                    st.session_state.is_admin = False
                    st.session_state.page = "Fazer Apostas"
                    st.rerun()
            else:
                st.error("Usuário não encontrado.")

    st.markdown("---")
    st.subheader("Não tem conta? Registre-se aqui (Jogadores)")
    with st.form("register_form"):
        new_username = st.text_input("Escolha um Nome de Usuário para Jogador", key="reg_username")
        reg_submitted = st.form_submit_button("Registrar")

        if reg_submitted:
            if new_username:
                if new_username.lower() == "admin":
                    st.error("Nome de usuário 'admin' é reservado.")
                elif new_username in st.session_state.users:
                    st.error("Este nome de usuário já existe.")
                else:
                    st.session_state.users[new_username] = {"password_hash": None, "is_admin": False} # Jogadores não usam senha nesta versão
                    save_data(USERS_FILE, st.session_state.users)
                    st.success(f"Usuário '{new_username}' registrado com sucesso! Faça o login.")
                    # Não precisa de rerun aqui, o usuário pode tentar logar.
            else:
                st.warning("Por favor, insira um nome de usuário para registrar.")

# --- Admin Section ---
def admin_settings_page():
    st.subheader("Configurações de Pontuação")
    settings = st.session_state.settings.copy() # Trabalhar com uma cópia

    settings["points_md1"] = st.number_input("Pontos por acertar MD1:", min_value=0, value=int(settings.get("points_md1", 2)))
    settings["points_md3_md5_winner"] = st.number_input("Pontos por acertar vencedor MD3/MD5 (placar errado):", min_value=0, value=int(settings.get("points_md3_md5_winner", 1)))
    settings["points_md3_md5_score"] = st.number_input("Pontos por acertar placar exato MD3/MD5:", min_value=0, value=int(settings.get("points_md3_md5_score", 5)))

    st.subheader("Gerenciar Senha do Admin")
    current_admin_password = st.text_input("Senha Atual do Admin", type="password", key="admin_curr_pass")
    new_admin_password = st.text_input("Nova Senha do Admin", type="password", key="admin_new_pass")
    confirm_new_admin_password = st.text_input("Confirmar Nova Senha do Admin", type="password", key="admin_conf_new_pass")

    if st.button("Salvar Configurações e Senha"):
        # Lógica de mudança de senha
        admin_user_data = st.session_state.users.get("admin")
        password_changed = False
        if admin_user_data:
            if current_admin_password or new_admin_password or confirm_new_admin_password: # Se algum campo de senha foi preenchido
                if not all([current_admin_password, new_admin_password, confirm_new_admin_password]):
                    st.warning("Para alterar a senha do admin, preencha todos os três campos de senha.")
                elif admin_user_data["password_hash"] == hash_password(current_admin_password):
                    if new_admin_password == confirm_new_admin_password:
                        if new_admin_password: # Garante que a nova senha não seja vazia
                            new_hash = hash_password(new_admin_password)
                            admin_user_data["password_hash"] = new_hash
                            settings["admin_password_hash"] = new_hash # Também atualiza nas settings gerais
                            st.session_state.users["admin"] = admin_user_data
                            save_data(USERS_FILE, st.session_state.users)
                            password_changed = True
                            st.success("Senha do admin atualizada com sucesso!")
                        else:
                            st.error("A nova senha não pode ser vazia.")
                    else:
                        st.error("As novas senhas não coincidem.")
                else:
                    st.error("Senha atual do admin incorreta.")
        
        # Salvar configurações gerais
        st.session_state.settings = settings
        save_data(SETTINGS_FILE, st.session_state.settings)
        if not password_changed and not (current_admin_password or new_admin_password or confirm_new_admin_password):
             st.success("Configurações de pontuação salvas!")
        elif password_changed:
             st.success("Configurações de pontuação e senha do admin salvas!")
        st.rerun()


def admin_manage_teams_page():
    st.subheader("Gerenciar Times")
    
    with st.form("add_team_form"):
        new_team = st.text_input("Nome do Novo Time", key="new_team_name")
        add_team_submitted = st.form_submit_button("Adicionar Time")
        if add_team_submitted:
            if new_team and new_team.strip() and new_team not in st.session_state.teams:
                st.session_state.teams.append(new_team.strip())
                st.session_state.teams.sort()
                save_data(TEAMS_FILE, st.session_state.teams)
                st.success(f"Time '{new_team.strip()}' adicionado.")
                st.rerun()
            elif not new_team or not new_team.strip():
                st.warning("Digite o nome do time.")
            else:
                st.error(f"Time '{new_team.strip()}' já existe.")

    st.write("Times Cadastrados:")
    if st.session_state.teams:
        teams_df = pd.DataFrame(st.session_state.teams, columns=["Nome do Time"])
        st.dataframe(teams_df, use_container_width=True, hide_index=True)
        
        team_to_delete = st.selectbox("Selecionar time para remover (CUIDADO!)", options=[""] + st.session_state.teams, key="delete_team_select", index=0)
        if team_to_delete and st.button(f"Remover Time '{team_to_delete}'"):
            team_in_match = any(match['team1'] == team_to_delete or match['team2'] == team_to_delete for match in st.session_state.matches)
            if team_in_match:
                st.error(f"Não é possível remover '{team_to_delete}'. O time está escalado em uma ou mais partidas. Remova/edite as partidas primeiro.")
            else:
                st.session_state.teams.remove(team_to_delete)
                save_data(TEAMS_FILE, st.session_state.teams)
                st.success(f"Time '{team_to_delete}' removido.")
                st.rerun()
    else:
        st.info("Nenhum time cadastrado.")


def admin_manage_matches_page():
    st.subheader("Gerenciar Partidas")
    
    if not st.session_state.teams or len(st.session_state.teams) < 2:
        st.warning("Você precisa cadastrar pelo menos dois times antes de criar partidas.")
        return

    with st.expander("Cadastrar Nova Partida", expanded=True):
        with st.form("add_match_form"):
            # Gera um ID único simples para a partida
            match_id_counter = max([m.get('id', 0) for m in st.session_state.matches] + [0]) + 1
            
            cols_teams = st.columns(2)
            team1 = cols_teams[0].selectbox("Time 1", options=st.session_state.teams, key="match_team1", index=0 if st.session_state.teams else None)
            
            # Garante que Time 2 não possa ser igual ao Time 1
            available_teams_for_team2 = [t for t in st.session_state.teams if t != team1] if team1 else st.session_state.teams
            team2_index = 0
            if available_teams_for_team2:
                 # Tenta manter uma seleção diferente se possível
                 if len(available_teams_for_team2) > 1 and st.session_state.teams.index(available_teams_for_team2[0]) == st.session_state.teams.index(team1 if team1 else -1) :
                     team2_index = 1 
            else: # Se só sobrou um time ou nenhum
                available_teams_for_team2 = ["Selecione Time 1 primeiro"] if not available_teams_for_team2 and team1 else available_teams_for_team2


            team2 = cols_teams[1].selectbox("Time 2", options=available_teams_for_team2, key="match_team2", index=team2_index if available_teams_for_team2 and team2_index < len(available_teams_for_team2) else 0)
            
            match_format = st.selectbox("Formato da Partida", options=["MD1", "MD3", "MD5"], key="match_format")
            # Usar st.date_input e st.time_input para melhor UX
            match_date = st.date_input("Data da Partida", value=None, key="match_date", help="Opcional. Usado para bloquear apostas.")
            match_time = st.time_input("Hora da Partida (Local)", value=None, key="match_time", help="Opcional. Use o fuso horário local.")
            
            match_group = st.text_input("Grupo/Fase (Ex: Play-In Rodada 1, Suíça Dia 2, Quartas)", key="match_group", value="")

            add_match_submitted = st.form_submit_button("Adicionar Partida")
            if add_match_submitted:
                if team1 and team2 and team1 != team2 and team1 in st.session_state.teams and team2 in st.session_state.teams :
                    dt_iso = None
                    if match_date and match_time:
                        # Combina data e hora, assume fuso local e converte para UTC ISO string para consistência
                        local_dt = datetime.combine(match_date, match_time)
                        # Para simplicidade, vamos armazenar como string ISO no fuso local.
                        # Para apps mais complexos, converter para UTC seria melhor:
                        # dt_iso = local_dt.astimezone(timezone.utc).isoformat()
                        dt_iso = local_dt.isoformat()
                    elif match_date: # Apenas data, sem hora específica
                        dt_iso = datetime.combine(match_date, datetime.min.time()).isoformat()


                    new_match = {
                        "id": match_id_counter,
                        "team1": team1,
                        "team2": team2,
                        "format": match_format,
                        "datetime_iso": dt_iso, # Armazena como string ISO
                        "group": match_group,
                        "status": "Agendada", # Agendada, Em Andamento, Finalizada
                        "result_team1_score": None,
                        "result_team2_score": None,
                        "winning_team": None
                    }
                    st.session_state.matches.append(new_match)
                    save_data(MATCHES_FILE, st.session_state.matches)
                    st.success("Partida adicionada!")
                    st.rerun()
                elif not team1 or not team2:
                    st.error("Selecione os dois times.")
                elif team1 == team2:
                    st.error("Os times 1 e 2 devem ser diferentes.")
                else:
                    st.error("Um ou ambos os times selecionados não são válidos. Verifique o cadastro de times.")


    st.markdown("---")
    st.subheader("Partidas Cadastradas e Resultados")
    if not st.session_state.matches:
        st.info("Nenhuma partida cadastrada.")
        return

    # Ordenar partidas: primeiro por data/hora (as mais recentes primeiro, ou as sem data por último), depois por ID.
    # Partidas sem data/hora são consideradas "posteriores" para ordenação.
    now_iso = datetime.now().isoformat()
    sorted_matches = sorted(
        st.session_state.matches, 
        key=lambda m: (m.get('datetime_iso') or 'zzzzzzzz', m['id']), # 'z' alto para colocar no final se None
        reverse=True # Mais recentes primeiro
    )


    for idx, match_obj in enumerate(sorted_matches):
        match_id = match_obj['id']
        container_key = f"match_container_{match_id}_{idx}" # Chave única para o container
        with st.container(): # Usar container para agrupar elementos de cada partida
            st.markdown("---")
            dt_display = "Não definida"
            is_past_deadline = False
            if match_obj['datetime_iso']:
                try:
                    # Assume que a string ISO já está no fuso horário correto ou é ingênua (local)
                    match_dt_obj = datetime.fromisoformat(match_obj['datetime_iso'])
                    dt_display = match_dt_obj.strftime("%d/%m/%Y %H:%M")
                    # Compara com o tempo atual local "ingênuo" se match_dt_obj for ingênuo
                    # Se match_dt_obj tiver fuso, converta now() para o mesmo fuso ou para UTC.
                    # Para simplificar, se a data armazenada for ingênua, comparamos com now() ingênuo.
                    current_time_local = datetime.now()
                    if match_dt_obj.tzinfo: # Se a data armazenada tem fuso
                        current_time_local = datetime.now(match_dt_obj.tzinfo) # Compara com o mesmo fuso
                    is_past_deadline = current_time_local > match_dt_obj
                except ValueError:
                    dt_display = f"Data inválida ({match_obj['datetime_iso']})"


            status_color = "blue"
            if match_obj['status'] == "Finalizada": status_color = "green"
            elif is_past_deadline and match_obj['status'] == "Agendada": status_color = "orange" # Passou do horário, mas não finalizada

            st.markdown(f"##### ID {match_id}: **{match_obj['team1']} vs {match_obj['team2']}** ({match_obj['format']}) - Grupo: *{match_obj.get('group','N/A')}*")
            st.markdown(f"Data/Hora: {dt_display} - Status: :{status_color}[{match_obj['status']}]")
            
            if match_obj['status'] == "Finalizada":
                st.write(f"Resultado: {match_obj['team1']} {match_obj['result_team1_score']} x {match_obj['result_team2_score']} {match_obj['team2']} (Vencedor: {match_obj.get('winning_team', 'N/A')})")

            # Expander para editar/registrar resultado
            with st.expander(f"Gerenciar Partida ID {match_id}", expanded=False):
                # Encontrar o índice original na lista não ordenada para salvar
                original_match_idx = next((i for i, m in enumerate(st.session_state.matches) if m['id'] == match_id), None)
                if original_match_idx is None: continue # Segurança

                current_match_data = st.session_state.matches[original_match_idx]

                # Editar informações básicas da partida (se não finalizada)
                if current_match_data['status'] != "Finalizada":
                    st.markdown("**Editar Informações da Partida**")
                    
                    edit_cols = st.columns(2)
                    # Edição de Times
                    current_t1_idx = st.session_state.teams.index(current_match_data['team1']) if current_match_data['team1'] in st.session_state.teams else 0
                    new_t1 = edit_cols[0].selectbox(f"Novo Time 1 (Atual: {current_match_data['team1']})", options=st.session_state.teams, index=current_t1_idx, key=f"edit_t1_{match_id}")
                    
                    available_edit_t2 = [t for t in st.session_state.teams if t != new_t1] if new_t1 else st.session_state.teams
                    current_t2_idx_val = current_match_data['team2']
                    new_t2_idx = available_edit_t2.index(current_t2_idx_val) if current_t2_idx_val in available_edit_t2 else 0
                    new_t2 = edit_cols[1].selectbox(f"Novo Time 2 (Atual: {current_match_data['team2']})", options=available_edit_t2, index=new_t2_idx, key=f"edit_t2_{match_id}")

                    # Edição de Formato e Grupo
                    format_options = ["MD1", "MD3", "MD5"]
                    current_fmt_idx = format_options.index(current_match_data['format']) if current_match_data['format'] in format_options else 0
                    new_fmt = st.selectbox(f"Novo Formato (Atual: {current_match_data['format']})", options=format_options, index=current_fmt_idx, key=f"edit_fmt_{match_id}")
                    
                    new_grp = st.text_input("Novo Grupo/Fase", value=current_match_data.get('group',''), key=f"edit_grp_{match_id}")

                    # Edição de Data/Hora
                    current_dt_val = None
                    current_time_val = None
                    if current_match_data['datetime_iso']:
                        try:
                            dt_obj = datetime.fromisoformat(current_match_data['datetime_iso'])
                            current_dt_val = dt_obj.date()
                            current_time_val = dt_obj.time()
                        except ValueError: pass # Mantém None se inválido

                    new_date = st.date_input("Nova Data", value=current_dt_val, key=f"edit_date_{match_id}")
                    new_time = st.time_input("Nova Hora", value=current_time_val, key=f"edit_time_{match_id}")

                    if st.button("Salvar Alterações da Partida", key=f"save_edit_match_{match_id}"):
                        if new_t1 and new_t2 and new_t1 != new_t2:
                            new_dt_iso = None
                            if new_date and new_time:
                                new_dt_iso = datetime.combine(new_date, new_time).isoformat()
                            elif new_date:
                                new_dt_iso = datetime.combine(new_date, datetime.min.time()).isoformat()
                            
                            st.session_state.matches[original_match_idx]['team1'] = new_t1
                            st.session_state.matches[original_match_idx]['team2'] = new_t2
                            st.session_state.matches[original_match_idx]['format'] = new_fmt
                            st.session_state.matches[original_match_idx]['datetime_iso'] = new_dt_iso
                            st.session_state.matches[original_match_idx]['group'] = new_grp
                            save_data(MATCHES_FILE, st.session_state.matches)
                            st.success(f"Partida ID {match_id} atualizada.")
                            st.rerun()
                        else:
                            st.error("Selecione dois times diferentes e válidos.")

                # Registrar/Editar Resultado
                st.markdown("**Registrar/Editar Resultado**")
                res_cols = st.columns(2)
                default_score1 = current_match_data.get('result_team1_score') if current_match_data.get('result_team1_score') is not None else 0
                default_score2 = current_match_data.get('result_team2_score') if current_match_data.get('result_team2_score') is not None else 0

                score1 = res_cols[0].number_input(f"Placar {current_match_data['team1']}", min_value=0, step=1, value=int(default_score1), key=f"res_s1_{match_id}")
                score2 = res_cols[1].number_input(f"Placar {current_match_data['team2']}", min_value=0, step=1, value=int(default_score2), key=f"res_s2_{match_id}")

                if st.button("Salvar Resultado e Calcular Pontos", key=f"save_res_{match_id}"):
                    valid_score_for_format = True
                    fmt = current_match_data['format']
                    if fmt == "MD1":
                        if not ((score1 == 1 and score2 == 0) or (score1 == 0 and score2 == 1)):
                            st.error("Placar inválido para MD1. Deve ser 1-0 ou 0-1.")
                            valid_score_for_format = False
                    elif fmt == "MD3": # 2-0, 2-1, 0-2, 1-2
                        if not (((score1 == 2 and score2 in [0,1]) or (score2 == 2 and score1 in [0,1])) and score1 != score2):
                            st.error("Placar inválido para MD3 (Ex: 2-0, 2-1, 0-2, 1-2).")
                            valid_score_for_format = False
                    elif fmt == "MD5": # 3-0, 3-1, 3-2, 0-3, 1-3, 2-3
                         if not (((score1 == 3 and score2 in [0,1,2]) or (score2 == 3 and score1 in [0,1,2])) and score1 != score2):
                            st.error("Placar inválido para MD5 (Ex: 3-0, 3-1, 3-2, 0-3, 1-3, 2-3).")
                            valid_score_for_format = False
                    
                    if score1 == score2 and valid_score_for_format : # Empate não é permitido
                        st.error("Empates não são permitidos no placar final.")
                        valid_score_for_format = False

                    if valid_score_for_format:
                        st.session_state.matches[original_match_idx]['result_team1_score'] = score1
                        st.session_state.matches[original_match_idx]['result_team2_score'] = score2
                        st.session_state.matches[original_match_idx]['status'] = "Finalizada"
                        if score1 > score2:
                            st.session_state.matches[original_match_idx]['winning_team'] = current_match_data['team1']
                        else: # score2 > score1
                            st.session_state.matches[original_match_idx]['winning_team'] = current_match_data['team2']
                        
                        calculate_points_for_match(match_id) # Calcula pontos para esta partida
                        save_data(MATCHES_FILE, st.session_state.matches)
                        save_data(BETS_FILE, st.session_state.bets) # Bets são atualizadas com pontos
                        st.success(f"Resultado da partida ID {match_id} salvo e pontos calculados!")
                        st.rerun()
                
                # Excluir Partida
                if st.button(f"Excluir Partida ID {match_id} (Irreversível)", type="primary", key=f"delete_match_{match_id}"):
                    # Remove a partida e todas as apostas associadas
                    st.session_state.bets = [b for b in st.session_state.bets if b['match_id'] != match_id]
                    st.session_state.matches.pop(original_match_idx)
                    save_data(MATCHES_FILE, st.session_state.matches)
                    save_data(BETS_FILE, st.session_state.bets)
                    st.warning(f"Partida ID {match_id} e todas as apostas associadas foram excluídas.")
                    st.rerun()


# --- Player Section ---
def player_make_bets_page():
    st.subheader(f"Fazer/Editar Apostas - Jogador: {st.session_state.logged_in_user}")
    
    # Partidas agendadas e cujo prazo de aposta não passou
    bettable_matches = []
    current_time = datetime.now() # Horário local ingênuo

    for m in st.session_state.matches:
        if m['status'] == "Agendada":
            can_bet = True
            if m['datetime_iso']:
                try:
                    match_dt = datetime.fromisoformat(m['datetime_iso'])
                    # Se match_dt tiver fuso, current_time precisa ser comparável (ou ambos UTC)
                    # Para esta versão, se match_dt é ingênuo, current_time também é.
                    if match_dt.tzinfo:
                         current_time_aware = datetime.now(match_dt.tzinfo)
                         if current_time_aware >= match_dt:
                            can_bet = False
                    elif current_time >= match_dt : # Comparação ingênua
                        can_bet = False
                except ValueError: # Data inválida, permite apostar por segurança (admin corrige)
                    pass 
            if can_bet:
                bettable_matches.append(m)
    
    if not bettable_matches:
        st.info("Nenhuma partida disponível para apostar no momento ou todas as apostas foram encerradas.")
        return

    # Ordenar por data/hora da partida
    bettable_matches_sorted = sorted(bettable_matches, key=lambda x: (x.get('datetime_iso') or 'zzzzzzzz', x['id']))

    for i, match in enumerate(bettable_matches_sorted):
        st.markdown("---")
        dt_display = "Não definida"
        if match['datetime_iso']:
            try:
                dt_display = datetime.fromisoformat(match['datetime_iso']).strftime('%d/%m/%Y %H:%M')
            except ValueError:
                dt_display = "Data inválida"
        
        st.markdown(f"**Partida ID {match['id']}: {match['team1']} vs {match['team2']}** ({match['format']})")
        st.caption(f"Grupo/Fase: *{match.get('group','N/A')}* | Prazo para aposta: {dt_display}")


        user_bet = next((b for b in st.session_state.bets if b['user_id'] == st.session_state.logged_in_user and b['match_id'] == match['id']), None)

        # Valores padrão para o formulário, baseados na aposta existente ou defaults
        default_winner = user_bet['predicted_winner'] if user_bet and user_bet['predicted_winner'] in [match['team1'], match['team2']] else match['team1']
        default_score1 = user_bet['predicted_score1'] if user_bet and user_bet['predicted_score1'] is not None else 0
        default_score2 = user_bet['predicted_score2'] if user_bet and user_bet['predicted_score2'] is not None else 0
        
        winner_options = [match['team1'], match['team2']]
        try:
            winner_idx = winner_options.index(default_winner)
        except ValueError: # Se o vencedor padrão não for uma das opções (ex: time mudou)
            winner_idx = 0 # Default para o primeiro time

        with st.form(key=f"bet_form_{match['id']}_{i}"):
            predicted_winner = st.radio("Vencedor Previsto:", winner_options, index=winner_idx, key=f"winner_{match['id']}", horizontal=True)
            
            pred_score1, pred_score2 = None, None
            max_score_val = 0

            if match['format'] == "MD3": max_score_val = 2
            elif match['format'] == "MD5": max_score_val = 3

            if match['format'] != "MD1":
                st.write("Placar Exato Previsto:")
                cols = st.columns(2)
                pred_score1 = cols[0].number_input(f"{match['team1']}", min_value=0, max_value=max_score_val, step=1, value=int(default_score1), key=f"pscore1_{match['id']}")
                pred_score2 = cols[1].number_input(f"{match['team2']}", min_value=0, max_value=max_score_val, step=1, value=int(default_score2), key=f"pscore2_{match['id']}")
            
            bet_button_label = "Atualizar Aposta" if user_bet else "Salvar Aposta"
            submit_bet = st.form_submit_button(bet_button_label)

            if submit_bet:
                is_valid_prediction = True
                # Validação do placar previsto
                if match['format'] != "MD1":
                    # Verifica se o placar é consistente com o vencedor previsto
                    if pred_score1 > pred_score2 and predicted_winner != match['team1']:
                        st.error(f"Conflito: Placar ({pred_score1}-{pred_score2}) indica {match['team1']} como vencedor, mas você selecionou {predicted_winner}.")
                        is_valid_prediction = False
                    elif pred_score2 > pred_score1 and predicted_winner != match['team2']:
                        st.error(f"Conflito: Placar ({pred_score1}-{pred_score2}) indica {match['team2']} como vencedor, mas você selecionou {predicted_winner}.")
                        is_valid_prediction = False
                    elif pred_score1 == pred_score2:
                        st.error("Empates não são permitidos no placar.")
                        is_valid_prediction = False
                    
                    # Validação específica do formato
                    if match['format'] == "MD3" and is_valid_prediction:
                        if not (((pred_score1 == 2 and pred_score2 in [0,1]) or (pred_score2 == 2 and pred_score1 in [0,1]))):
                            st.error(f"Placar previsto inválido para MD3. Deve ser 2-0, 2-1, 0-2 ou 1-2.")
                            is_valid_prediction = False
                    elif match['format'] == "MD5" and is_valid_prediction:
                        if not (((pred_score1 == 3 and pred_score2 in [0,1,2]) or (pred_score2 == 3 and pred_score1 in [0,1,2]))):
                            st.error(f"Placar previsto inválido para MD5. Deve ser 3-0, 3-1, 3-2, 0-3, 1-3 ou 2-3.")
                            is_valid_prediction = False
                
                if is_valid_prediction:
                    final_pred_score1 = pred_score1
                    final_pred_score2 = pred_score2
                    if match['format'] == "MD1": # Para MD1, placar é implícito pelo vencedor
                        final_pred_score1 = 1 if predicted_winner == match['team1'] else 0
                        final_pred_score2 = 1 if predicted_winner == match['team2'] else 0

                    bet_data = {
                        "user_id": st.session_state.logged_in_user,
                        "match_id": match['id'],
                        "predicted_winner": predicted_winner,
                        "predicted_score1": final_pred_score1,
                        "predicted_score2": final_pred_score2,
                        "points_awarded": 0 # Calculado depois
                    }
                    
                    existing_bet_idx = next((idx for idx, b_item in enumerate(st.session_state.bets) if b_item['user_id'] == st.session_state.logged_in_user and b_item['match_id'] == match['id']), None)
                    if existing_bet_idx is not None:
                        st.session_state.bets[existing_bet_idx] = bet_data
                        st.success(f"Aposta para a partida ID {match['id']} atualizada!")
                    else:
                        st.session_state.bets.append(bet_data)
                        st.success(f"Aposta para a partida ID {match['id']} salva!")
                    
                    save_data(BETS_FILE, st.session_state.bets)
                    st.rerun()


def player_my_bets_page():
    st.subheader(f"Minhas Apostas - {st.session_state.logged_in_user}")
    user_bets = [b for b in st.session_state.bets if b['user_id'] == st.session_state.logged_in_user]

    if not user_bets:
        st.info("Você ainda não fez nenhuma aposta.")
        return

    my_bets_data = []
    # Ordenar apostas por ID da partida
    for bet in sorted(user_bets, key=lambda x: x['match_id']):
        match_info = next((m for m in st.session_state.matches if m['id'] == bet['match_id']), None)
        if match_info:
            score_pred_display = f"{bet['predicted_score1']}-{bet['predicted_score2']}"
            if match_info['format'] == "MD1": # Para MD1, o placar é sempre 1-0 ou 0-1, não precisa mostrar explicitamente a aposta de placar.
                 score_pred_display = "N/A (MD1)"


            result_actual_display = "Pendente"
            points_display = "Pendente"
            if match_info['status'] == "Finalizada":
                 result_actual_display = f"{match_info['team1']} {match_info['result_team1_score']} x {match_info['result_team2_score']} {match_info['team2']} (Vencedor: {match_info.get('winning_team', 'N/A')})"
                 points_display = bet.get('points_awarded', 0)

            my_bets_data.append({
                "ID Partida": match_info['id'],
                "Partida": f"{match_info['team1']} vs {match_info['team2']} ({match_info['format']})",
                "Meu Vencedor": bet['predicted_winner'],
                "Meu Placar": score_pred_display,
                "Resultado Real": result_actual_display,
                "Pontos Ganhos": points_display
            })
    
    if my_bets_data:
        bets_df = pd.DataFrame(my_bets_data)
        st.dataframe(bets_df, use_container_width=True, hide_index=True)
    else:
        st.info("Não foi possível carregar informações das suas apostas.")


def calculate_points_for_match(match_id):
    """Calcula pontos para todos os usuários que apostaram em uma partida finalizada específica."""
    match_obj = next((m for m in st.session_state.matches if m['id'] == match_id and m['status'] == "Finalizada"), None)
    if not match_obj:
        st.warning(f"Tentativa de calcular pontos para partida ID {match_id} não encontrada ou não finalizada.")
        return

    settings = st.session_state.settings
    actual_winner = match_obj['winning_team']
    actual_score1 = match_obj['result_team1_score']
    actual_score2 = match_obj['result_team2_score']

    for bet_idx, bet in enumerate(st.session_state.bets):
        if bet['match_id'] == match_id:
            points = 0
            predicted_winner = bet['predicted_winner']
            predicted_score1 = bet['predicted_score1']
            predicted_score2 = bet['predicted_score2']

            correct_winner_guess = (predicted_winner == actual_winner)

            if match_obj['format'] == "MD1":
                if correct_winner_guess:
                    points = settings.get("points_md1", 2)
            else: # MD3 or MD5
                correct_score_guess = (predicted_score1 == actual_score1 and predicted_score2 == actual_score2)
                if correct_winner_guess and correct_score_guess:
                    points = settings.get("points_md3_md5_score", 5)
                elif correct_winner_guess: # Acertou vencedor, errou placar
                    points = settings.get("points_md3_md5_winner", 1)
            
            st.session_state.bets[bet_idx]['points_awarded'] = points
    # A função que chama calculate_points_for_match (admin_manage_matches_page) já salva os bets.


def show_ranking_page():
    st.subheader("Ranking Geral do Bolão")
    
    if not st.session_state.users: # Se não há usuários, não há ranking
        st.info("Nenhum jogador registrado para exibir no ranking.")
        return

    player_scores = defaultdict(int)
    # Inicializa todos os jogadores (não admin) com 0 pontos
    for username, user_data in st.session_state.users.items():
        if not user_data.get("is_admin", False):
            player_scores[username] = 0

    # Soma os pontos das apostas de partidas finalizadas
    for bet in st.session_state.bets:
        match_info = next((m for m in st.session_state.matches if m['id'] == bet['match_id']), None)
        user_info = st.session_state.users.get(bet['user_id'])
        
        if match_info and match_info['status'] == "Finalizada" and user_info and not user_info.get("is_admin", False):
            player_scores[bet['user_id']] += bet.get('points_awarded', 0)
    
    if not player_scores: # Se defaultdict ainda está vazio (ex: só admin existe ou nenhuma partida finalizada)
        st.info("Nenhum ponto computado ainda ou não há jogadores participantes.")
        return

    # Ordena jogadores por pontuação (maior primeiro), depois alfabeticamente
    sorted_players = sorted(player_scores.items(), key=lambda item: (-item[1], item[0])) 
    
    ranking_data = [{"Posição": i+1, "Jogador": player, "Pontos": score} for i, (player, score) in enumerate(sorted_players)]
    
    if ranking_data:
        ranking_df = pd.DataFrame(ranking_data)
        st.dataframe(ranking_df, use_container_width=True, hide_index=True)
    else: # Caso raro, mas pode acontecer se todos os jogadores tiverem 0 pontos e não houver apostas.
        st.info("Ranking indisponível. Verifique se há jogadores e partidas finalizadas com apostas.")

# --- Admin Dashboard ---
def admin_dashboard_page():
    st.title(f"Dashboard do Administrador - {st.session_state.logged_in_user}")
    st.write("Bem-vindo à área de administração do bolão do Mundial de LoL!")
    
    num_players = len([u for u, data in st.session_state.users.items() if not data.get("is_admin")])
    num_teams = len(st.session_state.teams)
    num_matches_total = len(st.session_state.matches)
    num_matches_pending = len([m for m in st.session_state.matches if m['status'] == "Agendada"])
    num_matches_finished = len([m for m in st.session_state.matches if m['status'] == "Finalizada"])
    num_bets_total = len(st.session_state.bets)

    cols_metrics1 = st.columns(3)
    cols_metrics1[0].metric("Jogadores Registrados", num_players)
    cols_metrics1[1].metric("Times Cadastrados", num_teams)
    cols_metrics1[2].metric("Total de Apostas Feitas", num_bets_total)
    
    cols_metrics2 = st.columns(3)
    cols_metrics2[0].metric("Partidas Cadastradas", num_matches_total)
    cols_metrics2[1].metric("Partidas Pendentes/Agendadas", num_matches_pending)
    cols_metrics2[2].metric("Partidas Finalizadas", num_matches_finished)

    st.markdown("---")
    st.info("Utilize o menu na barra lateral para navegar pelas funcionalidades de administração.")


# --- Main App Logic ---
def main():
    st.set_page_config(layout="wide", page_title="Bolão Worlds 5BAG", initial_sidebar_state="expanded")
    initialize_session_state() # Garante que tudo seja carregado uma vez

    if not st.session_state.logged_in_user:
        login_page()
    else:
        user = st.session_state.logged_in_user
        is_admin = st.session_state.is_admin

        st.sidebar.header(f"Bolão Worlds 5BAG")
        st.sidebar.markdown(f"Usuário: **{user}**")
        st.sidebar.caption(f"Status: {'Administrador' if is_admin else 'Jogador'}")
        st.sidebar.markdown("---")


        # Navegação
        if is_admin:
            admin_pages_options = {
                "Dashboard Admin": admin_dashboard_page,
                "Gerenciar Times": admin_manage_teams_page,
                "Gerenciar Partidas": admin_manage_matches_page,
                "Configurações do Bolão": admin_settings_page,
                "Fazer Apostas (Visão Admin)": player_make_bets_page, # Admin também pode apostar
                "Minhas Apostas (Visão Admin)": player_my_bets_page,
                "Ranking Geral": show_ranking_page
            }
            # Define a página padrão para admin se a atual não for válida
            if st.session_state.page not in admin_pages_options:
                st.session_state.page = "Dashboard Admin"
            
            current_page_selection = st.sidebar.radio("Menu Administrador", 
                                                      options=list(admin_pages_options.keys()), 
                                                      key="admin_nav",
                                                      index=list(admin_pages_options.keys()).index(st.session_state.page))
            if current_page_selection != st.session_state.page: # Atualiza a página se a seleção mudou
                 st.session_state.page = current_page_selection
                 st.rerun() # Garante que a página correta seja renderizada
            
            admin_pages_options[st.session_state.page]() # Executa a função da página selecionada

        else: # Jogador
            player_pages_options = {
                "Fazer Apostas": player_make_bets_page,
                "Minhas Apostas": player_my_bets_page,
                "Ranking Geral": show_ranking_page
            }
            # Define a página padrão para jogador se a atual não for válida
            if st.session_state.page not in player_pages_options:
                st.session_state.page = "Fazer Apostas"

            current_page_selection = st.sidebar.radio("Menu Jogador", 
                                                      options=list(player_pages_options.keys()), 
                                                      key="player_nav",
                                                      index=list(player_pages_options.keys()).index(st.session_state.page))
            if current_page_selection != st.session_state.page:
                 st.session_state.page = current_page_selection
                 st.rerun()

            player_pages_options[st.session_state.page]()

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            # Limpa o estado da sessão relacionado ao login
            for key in ['logged_in_user', 'is_admin', 'page']:
                if key in st.session_state:
                    del st.session_state[key]
            # Poderia limpar outros dados da sessão se necessário, mas para este app,
            # o initialize_session_state vai recarregar os dados dos arquivos na próxima vez.
            st.rerun()

if __name__ == "__main__":
    main()