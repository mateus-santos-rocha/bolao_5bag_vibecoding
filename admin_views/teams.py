# Arquivo: admin_views/teams.py
# Descrição: Página de gerenciamento de times do campeonato.

import streamlit as st
import pandas as pd
from data_utils import save_data
from constants import TEAMS_BASENAME
# slugify pode ser movido para um utils.py global se necessário em mais lugares
import re 

def slugify_teams(text): # Renomeado para evitar conflito se outro slugify for importado
    if not isinstance(text, str): return "invalid_id"
    text = text.lower()
    text = re.sub(r'\s+', '_', text) 
    text = re.sub(r'[^\w-]', '', text) 
    return text if text else "unnamed_id"

def admin_manage_teams_page(championship_id, championship_name):
    """Renderiza a página de gerenciamento de times para o campeonato ativo."""
    st.subheader(f"Gerenciar Times - Campeonato: {championship_name}")
    
    teams_list_teams_page = st.session_state.get("teams", []) # Renomeado para evitar conflito

    with st.form(f"add_team_form_teams_page_{championship_id}"): # Renomeado
        new_team_teams_page = st.text_input("Nome do Novo Time", key=f"new_team_name_teams_page_{championship_id}") # Renomeado
        add_team_submitted_teams_page = st.form_submit_button("Adicionar Time") # Renomeado
        if add_team_submitted_teams_page:
            if new_team_teams_page and new_team_teams_page.strip() and new_team_teams_page.strip() not in teams_list_teams_page:
                teams_list_teams_page.append(new_team_teams_page.strip())
                teams_list_teams_page.sort()
                st.session_state.teams = teams_list_teams_page
                save_data(TEAMS_BASENAME, teams_list_teams_page, championship_id=championship_id)
                st.success(f"Time '{new_team_teams_page.strip()}' adicionado ao campeonato '{championship_name}'.")
                st.rerun()
            elif not new_team_teams_page or not new_team_teams_page.strip():
                st.warning("Digite o nome do time.")
            else:
                st.error(f"Time '{new_team_teams_page.strip()}' já existe neste campeonato.")

    st.write("Times Cadastrados no Campeonato:")
    if teams_list_teams_page:
        teams_df_teams_page = pd.DataFrame(teams_list_teams_page, columns=["Nome do Time"]) # Renomeado
        st.dataframe(teams_df_teams_page, use_container_width=True, hide_index=True)
        
        team_to_delete_teams_page = st.selectbox("Selecionar time para remover", options=[""] + teams_list_teams_page, key=f"delete_team_select_teams_page_{championship_id}", index=0) # Renomeado
        if team_to_delete_teams_page and st.button(f"Remover '{team_to_delete_teams_page}'", key=f"btn_delete_team_teams_page_{championship_id}_{slugify_teams(team_to_delete_teams_page)}"): # Renomeado, usa slugify_teams
            matches_this_champ_teams_page = st.session_state.get("matches", []) # Renomeado
            team_in_match_teams_page = any(match.get('team1') == team_to_delete_teams_page or match.get('team2') == team_to_delete_teams_page for match in matches_this_champ_teams_page) # Renomeado
            if team_in_match_teams_page:
                st.error(f"Não é possível remover '{team_to_delete_teams_page}'. O time está em partidas deste campeonato.")
            else:
                teams_list_teams_page.remove(team_to_delete_teams_page)
                st.session_state.teams = teams_list_teams_page
                save_data(TEAMS_BASENAME, teams_list_teams_page, championship_id=championship_id)
                st.success(f"Time '{team_to_delete_teams_page}' removido do campeonato '{championship_name}'.")
                st.rerun()
    else:
        st.info("Nenhum time cadastrado para este campeonato.")

# --- FIM DO ARQUIVO: admin_views/teams.py ---