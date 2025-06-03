# Arquivo: bolao_lol.py
# Descrição: Arquivo principal do aplicativo Streamlit Bolão LoL Worlds.

import streamlit as st

from constants import (DEFAULT_CHAMPIONSHIP_SETTINGS, DEFAULT_APP_CONFIG, DEFAULT_ADMIN_PASSWORD,
                       USERS_BASENAME, CHAMPIONSHIPS_BASENAME, APP_CONFIG_BASENAME, 
                       TEAMS_BASENAME, MATCHES_BASENAME, BETS_BASENAME, 
                       CHAMPIONSHIP_SETTINGS_BASENAME, LATE_BET_REQUESTS_BASENAME) 
from data_utils import load_data, save_data
from auth import login_page, hash_password 

# Importações dos submódulos de admin_views
from admin_views.championships import admin_manage_championships_page
from admin_views.dashboard import admin_dashboard_page
from admin_views.teams import admin_manage_teams_page
from admin_views.matches import admin_manage_matches_page
from admin_views.settings import admin_settings_page
from admin_views.late_requests import admin_manage_late_requests_page

from player_pages import player_make_bets_page, player_my_bets_page
from shared_pages import show_ranking_page, show_evolution_page # Adicionar show_evolution_page


def load_championship_data(championship_id_to_load): 
    if championship_id_to_load:
        st.session_state.teams = load_data(TEAMS_BASENAME, championship_id=championship_id_to_load, default_data_factory=lambda: [])
        st.session_state.matches = load_data(MATCHES_BASENAME, championship_id=championship_id_to_load, default_data_factory=lambda: [])
        st.session_state.bets = load_data(BETS_BASENAME, championship_id=championship_id_to_load, default_data_factory=lambda: [])
        
        loaded_champ_settings = load_data(CHAMPIONSHIP_SETTINGS_BASENAME, championship_id=championship_id_to_load, default_data_factory=lambda: DEFAULT_CHAMPIONSHIP_SETTINGS.copy())
        default_settings_copy = DEFAULT_CHAMPIONSHIP_SETTINGS.copy() 
        if not loaded_champ_settings: 
            st.session_state.championship_settings = default_settings_copy
            save_data(CHAMPIONSHIP_SETTINGS_BASENAME, default_settings_copy, championship_id=championship_id_to_load)
        else: 
            for key, value in default_settings_copy.items():
                if key not in loaded_champ_settings:
                    loaded_champ_settings[key] = value
            st.session_state.championship_settings = loaded_champ_settings

        st.session_state.late_bet_requests = load_data(LATE_BET_REQUESTS_BASENAME, championship_id=championship_id_to_load, default_data_factory=lambda: [])
        st.session_state.loaded_for_championship_id = championship_id_to_load 
    else: 
        keys_to_clear = ['teams', 'matches', 'bets', 'championship_settings', 'late_bet_requests']
        for key_clear in keys_to_clear:
            st.session_state[key_clear] = [] if key_clear not in ['championship_settings'] else {}
        st.session_state.loaded_for_championship_id = None


def initialize_session_state():
    if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False
    if 'page' not in st.session_state: st.session_state.page = "Login"
    
    if 'admin_selected_championship_id' not in st.session_state: 
        st.session_state.admin_selected_championship_id = None 
    
    if 'app_config' not in st.session_state:
        st.session_state.app_config = load_data(APP_CONFIG_BASENAME, default_data_factory=lambda: DEFAULT_APP_CONFIG.copy())
        if not st.session_state.app_config.get("admin_password_hash"): 
             st.session_state.app_config = DEFAULT_APP_CONFIG.copy()
             save_data(APP_CONFIG_BASENAME, st.session_state.app_config)

    if 'users' not in st.session_state:
        users_data = load_data(USERS_BASENAME, default_data_factory=lambda: {})
        admin_pass_hash_default = hash_password(DEFAULT_ADMIN_PASSWORD) 
        admin_pass_hash = st.session_state.app_config.get("admin_password_hash", admin_pass_hash_default)
        
        admin_entry = users_data.get("admin", {})
        if not users_data or "admin" not in users_data or admin_entry.get("password_hash") != admin_pass_hash or not admin_entry.get("is_admin"):
            users_data["admin"] = {"password_hash": admin_pass_hash, "is_admin": True}
            save_data(USERS_BASENAME, users_data) 
        st.session_state.users = users_data

    if 'championships' not in st.session_state:
        st.session_state.championships = load_data(CHAMPIONSHIPS_BASENAME, default_data_factory=lambda: [])

    if 'live_championship_id' not in st.session_state:
        st.session_state.live_championship_id = None
        st.session_state.live_championship_name = ""
        champs = st.session_state.get("championships", [])
        for champ_data_init in champs: 
            if isinstance(champ_data_init, dict) and champ_data_init.get("is_active_for_players"):
                st.session_state.live_championship_id = champ_data_init.get("id")
                st.session_state.live_championship_name = champ_data_init.get("name")
                break
    
    if 'loaded_for_championship_id' not in st.session_state:
        st.session_state.loaded_for_championship_id = None

    champ_id_to_use_for_data = None
    if st.session_state.get("is_admin"):
        champ_id_to_use_for_data = st.session_state.get("admin_selected_championship_id")
    else: 
        champ_id_to_use_for_data = st.session_state.get("live_championship_id")

    if (champ_id_to_use_for_data and st.session_state.loaded_for_championship_id != champ_id_to_use_for_data) or \
       ('teams' not in st.session_state and champ_id_to_use_for_data): 
        load_championship_data(champ_id_to_use_for_data)
    elif not champ_id_to_use_for_data and st.session_state.loaded_for_championship_id is not None:
        load_championship_data(None)
    elif 'teams' not in st.session_state : 
        load_championship_data(champ_id_to_use_for_data) 


def main():
    st.set_page_config(layout="wide", page_title="Bolão LoL Worlds", initial_sidebar_state="expanded")
    initialize_session_state()

    user = st.session_state.logged_in_user
    is_admin = st.session_state.is_admin
    
    effective_championship_id = None
    effective_championship_name = ""

    if is_admin:
        effective_championship_id = st.session_state.get("admin_selected_championship_id")
        if effective_championship_id:
            champ_info = next((c for c in st.session_state.get("championships", []) if c.get("id") == effective_championship_id), None)
            if champ_info: effective_championship_name = champ_info.get("name", "")
    else: 
        effective_championship_id = st.session_state.get("live_championship_id")
        effective_championship_name = st.session_state.get("live_championship_name", "")


    if not user: 
        login_page()
    else:
        st.sidebar.header(f"Bolão LoL Worlds")
        st.sidebar.markdown(f"Usuário: **{user}**")
        st.sidebar.caption(f"Status: {'Administrador' if is_admin else 'Jogador'}")
        
        if effective_championship_name and not (is_admin and st.session_state.page == "Gerenciar Campeonatos"):
            st.sidebar.markdown(f"Campeonato: **{effective_championship_name}**")
        elif is_admin and st.session_state.page != "Gerenciar Campeonatos" and not effective_championship_id:
             st.sidebar.warning("Nenhum camp. selecionado!")
        elif not is_admin and not effective_championship_id:
             st.sidebar.info("Nenhum camp. ativo para jogadores.")

        st.sidebar.markdown("---")

        admin_pages_map = { 
            "Gerenciar Campeonatos": lambda: admin_manage_championships_page(), 
            "Dashboard Admin": lambda: admin_dashboard_page(effective_championship_id, effective_championship_name),
            "Gerenciar Times": lambda: admin_manage_teams_page(effective_championship_id, effective_championship_name),
            "Gerenciar Partidas": lambda: admin_manage_matches_page(effective_championship_id, effective_championship_name),
            "Solicitações de Aposta Tardia": lambda: admin_manage_late_requests_page(effective_championship_id, effective_championship_name),
            "Configurações do Campeonato": lambda: admin_settings_page(effective_championship_id, effective_championship_name),
            "Ranking Geral (Visão Admin)": lambda: show_ranking_page(effective_championship_id, effective_championship_name),
            "Evolução dos Jogadores (Admin)": lambda: show_evolution_page(effective_championship_id, effective_championship_name), # NOVA PÁGINA
            "Fazer Apostas (Visão Admin)": lambda: player_make_bets_page(effective_championship_id, effective_championship_name),
            "Minhas Apostas (Visão Admin)": lambda: player_my_bets_page(effective_championship_id, effective_championship_name),
        }
        
        player_pages_map = { 
            "Fazer Apostas": lambda: player_make_bets_page(effective_championship_id, effective_championship_name),
            "Minhas Apostas": lambda: player_my_bets_page(effective_championship_id, effective_championship_name),
            "Ranking Geral": lambda: show_ranking_page(effective_championship_id, effective_championship_name),
            "Evolução dos Jogadores": lambda: show_evolution_page(effective_championship_id, effective_championship_name) # NOVA PÁGINA
        }

        current_pages_map = admin_pages_map if is_admin else player_pages_map 
        default_page = "Gerenciar Campeonatos" if is_admin else "Fazer Apostas" 
        menu_title = "Menu Administrador" if is_admin else "Menu Jogador" 
        nav_key = "admin_nav_main_key_v4" if is_admin else "player_nav_main_key_v4"

        if st.session_state.page not in current_pages_map:
            st.session_state.page = default_page
        
        try:
            current_page_index = list(current_pages_map.keys()).index(st.session_state.page)
        except ValueError: 
            st.session_state.page = default_page
            current_page_index = list(current_pages_map.keys()).index(st.session_state.page)

        selected_page = st.sidebar.radio( 
            menu_title, 
            options=list(current_pages_map.keys()), 
            key=nav_key,
            index=current_page_index
        )

        if selected_page != st.session_state.page:
             st.session_state.page = selected_page
             st.rerun()
        
        page_function = current_pages_map[st.session_state.page] 
        
        can_render = True
        if is_admin and st.session_state.page != "Gerenciar Campeonatos" and not effective_championship_id:
            st.warning("Por favor, selecione um campeonato na página 'Gerenciar Campeonatos' para continuar.")
            can_render = False
        elif not is_admin and not effective_championship_id: 
            st.warning("Nenhum campeonato está ativo para visualização ou apostas. Por favor, contate o administrador.")
            can_render = False
        
        if can_render:
            page_function()

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            keys_to_clear = ['logged_in_user', 'is_admin', 'page', 'admin_selected_championship_id', 
                             'live_championship_id', 'live_championship_name', 'loaded_for_championship_id',
                             'teams', 'matches', 'bets', 'championship_settings', 'late_bet_requests']
            for k_clear in keys_to_clear: 
                if k_clear in st.session_state:
                    del st.session_state[k_clear]
            st.rerun()

if __name__ == "__main__":
    main()

# --- FIM DO ARQUIVO: bolao_lol.py ---