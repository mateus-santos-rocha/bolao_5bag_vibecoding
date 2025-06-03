# Arquivo: admin_views/matches.py
# Descrição: Página de gerenciamento de partidas.

import streamlit as st
import pandas as pd # Adicionado, pode ser útil para listar partidas
from datetime import datetime
from data_utils import save_data
from constants import MATCHES_BASENAME, BETS_BASENAME # Adicionado BETS_BASENAME
from logic import calculate_points_for_match

def admin_manage_matches_page(championship_id, championship_name):
    """Renderiza a página de gerenciamento de partidas para o campeonato ativo."""
    st.subheader(f"Gerenciar Partidas - Campeonato: {championship_name}")
    
    current_teams = st.session_state.get("teams", [])
    current_matches = st.session_state.get("matches", [])

    if not current_teams or len(current_teams) < 2:
        st.warning("Você precisa cadastrar pelo menos dois times neste campeonato antes de criar partidas.")
        if st.button(f"Gerenciar Times de {championship_name}", key=f"goto_teams_matches_page_{championship_id}"): # Chave única
            st.session_state.page = "Gerenciar Times" 
            st.rerun()
        return

    with st.expander("Cadastrar Nova Partida", expanded=True):
        with st.form(f"add_match_form_{championship_id}"):
            match_id_counter = max([m.get('id', 0) for m in current_matches] + [0]) + 1
            
            cols_teams_add = st.columns(2) # Renomeado
            team1_add = cols_teams_add[0].selectbox("Time 1", options=current_teams, key=f"match_team1_add_form_{championship_id}", index=0 if current_teams else None) # Chave única
            
            available_teams_for_team2_add = [t for t in current_teams if t != team1_add] if team1_add else current_teams # Renomeado
            team2_index_add = 0 # Renomeado
            if available_teams_for_team2_add and team1_add and len(available_teams_for_team2_add) > 0 :
                 if available_teams_for_team2_add[0] == team1_add : 
                     if len(available_teams_for_team2_add) > 1: team2_index_add = 1 
            
            team2_add = cols_teams_add[1].selectbox("Time 2", options=available_teams_for_team2_add, key=f"match_team2_add_form_{championship_id}", index=team2_index_add if available_teams_for_team2_add and team2_index_add < len(available_teams_for_team2_add) else 0) # Chave única
            
            match_format_add = st.selectbox("Formato", options=["MD1", "MD3", "MD5"], key=f"match_format_add_form_{championship_id}") # Chave única
            match_date_add = st.date_input("Data", value=None, key=f"match_date_add_form_{championship_id}") # Chave única
            match_time_add = st.time_input("Hora (Local)", value=None, key=f"match_time_add_form_{championship_id}") # Chave única
            match_group_add = st.text_input("Grupo/Fase", key=f"match_group_add_form_{championship_id}", value="") # Chave única

            add_match_submitted_form_btn = st.form_submit_button("Adicionar Partida") # Renomeado
            if add_match_submitted_form_btn:
                if team1_add and team2_add and team1_add != team2_add and team1_add in current_teams and team2_add in current_teams:
                    dt_iso_add = None # Renomeado
                    if match_date_add and match_time_add: dt_iso_add = datetime.combine(match_date_add, match_time_add).isoformat()
                    elif match_date_add: dt_iso_add = datetime.combine(match_date_add, datetime.min.time()).isoformat()

                    new_match_item = { # Renomeado
                        "id": match_id_counter, "team1": team1_add, "team2": team2_add, "format": match_format_add,
                        "datetime_iso": dt_iso_add, "group": match_group_add, "status": "Agendada",
                        "result_team1_score": None, "result_team2_score": None, "winning_team": None
                    }
                    current_matches.append(new_match_item)
                    st.session_state.matches = current_matches
                    save_data(MATCHES_BASENAME, current_matches, championship_id=championship_id)
                    st.success("Partida adicionada!"); st.rerun()
                elif not team1_add or not team2_add: st.error("Selecione os dois times.")
                elif team1_add == team2_add: st.error("Os times 1 e 2 devem ser diferentes.")
                else: st.error("Um ou ambos os times selecionados não são válidos para este campeonato.")

    st.markdown("---"); st.subheader("Partidas Cadastradas")
    if not current_matches: st.info("Nenhuma partida cadastrada para este campeonato."); return

    sorted_matches_list_disp = sorted(current_matches, key=lambda m: (m.get('datetime_iso') or 'zzzzzzzz', m.get('id',0)), reverse=True) # Renomeado

    for idx_disp, match_obj_disp in enumerate(sorted_matches_list_disp): # Renomeado
        match_id_disp = match_obj_disp.get('id') # Renomeado
        if match_id_disp is None: continue

        with st.container(): 
            st.markdown("---") 
            dt_display_val = "Não definida"; is_past_val = False # Renomeado
            if match_obj_disp.get('datetime_iso'):
                try:
                    match_dt_obj_val = datetime.fromisoformat(match_obj_disp['datetime_iso']) # Renomeado
                    dt_display_val = match_dt_obj_val.strftime("%d/%m/%Y %H:%M")
                    current_time_val = datetime.now() # Renomeado
                    if match_dt_obj_val.tzinfo: current_time_val = datetime.now(match_dt_obj_val.tzinfo)
                    is_past_val = current_time_val > match_dt_obj_val
                except ValueError: dt_display_val = f"Data inválida ({match_obj_disp.get('datetime_iso')})"
            
            status_color_val = "blue" # Renomeado
            if match_obj_disp.get('status') == "Finalizada": status_color_val = "green"
            elif is_past_val and match_obj_disp.get('status') == "Agendada": status_color_val = "orange"

            st.markdown(f"##### ID {match_id_disp}: **{match_obj_disp.get('team1','T1?')} vs {match_obj_disp.get('team2','T2?')}** ({match_obj_disp.get('format','FMT?')})")
            st.markdown(f"Grupo/Fase: *{match_obj_disp.get('group','N/A')}* | Data/Hora: {dt_display_val} | Status: :{status_color_val}[{match_obj_disp.get('status','?')}]")
            if match_obj_disp.get('status') == "Finalizada":
                st.write(f"Resultado: **{match_obj_disp.get('team1','T1?')} {match_obj_disp.get('result_team1_score','?')}** x **{match_obj_disp.get('result_team2_score','?')} {match_obj_disp.get('team2','T2?')}** (Vencedor: **{match_obj_disp.get('winning_team', 'N/A')}**)")

            exp_key_match_manage = f"expander_match_manage_{match_id_disp}_{championship_id}" # Renomeado
            with st.expander(f"Gerenciar Partida ID {match_id_disp}", key=exp_key_match_manage):
                original_match_idx_manage = next((i for i, m_item_manage in enumerate(st.session_state.matches) if m_item_manage.get('id') == match_id_disp), None) # Renomeado
                if original_match_idx_manage is None: 
                    st.error("Erro ao encontrar partida para gerenciar."); continue
                
                current_match_data_manage = st.session_state.matches[original_match_idx_manage] # Renomeado

                if current_match_data_manage.get('status') != "Finalizada":
                    st.markdown(f"**Editar Informações da Partida**")
                    with st.form(key=f"edit_match_form_inn_{match_id_disp}_{championship_id}"): # Renomeado
                        edit_cols_form_inn = st.columns(2) # Renomeado
                        current_t1_val_inn = current_match_data_manage.get('team1')
                        current_t1_idx_inn = current_teams.index(current_t1_val_inn) if current_t1_val_inn in current_teams else 0
                        new_t1_form_inn = edit_cols_form_inn[0].selectbox("Time 1", current_teams, index=current_t1_idx_inn, key=f"form_inn_edit_t1_{match_id_disp}_{championship_id}")
                        
                        available_t2_form_inn = [t for t in current_teams if t != new_t1_form_inn] if new_t1_form_inn else current_teams
                        current_t2_val_inn = current_match_data_manage.get('team2')
                        current_t2_idx_inn = available_t2_form_inn.index(current_t2_val_inn) if current_t2_val_inn in available_t2_form_inn else 0
                        new_t2_form_inn = edit_cols_form_inn[1].selectbox("Time 2", available_t2_form_inn, index=current_t2_idx_inn, key=f"form_inn_edit_t2_{match_id_disp}_{championship_id}")
                        
                        new_fmt_form_inn = st.selectbox("Formato", ["MD1","MD3","MD5"], index=["MD1","MD3","MD5"].index(current_match_data_manage.get('format','MD1')), key=f"form_inn_edit_fmt_{match_id_disp}_{championship_id}")
                        new_grp_form_inn = st.text_input("Grupo/Fase", value=current_match_data_manage.get('group',''), key=f"form_inn_edit_grp_{match_id_disp}_{championship_id}")
                        
                        dt_iso_val_inn = current_match_data_manage.get('datetime_iso')
                        current_dt_inn, current_tm_inn = None, None
                        if dt_iso_val_inn:
                            try: 
                                dt_obj_inn = datetime.fromisoformat(dt_iso_val_inn)
                                current_dt_inn, current_tm_inn = dt_obj_inn.date(), dt_obj_inn.time()
                            except: pass
                        new_dt_form_inn = st.date_input("Nova Data", value=current_dt_inn, key=f"form_inn_edit_dt_{match_id_disp}_{championship_id}")
                        new_tm_form_inn = st.time_input("Nova Hora", value=current_tm_inn, key=f"form_inn_edit_tm_{match_id_disp}_{championship_id}")

                        if st.form_submit_button("Salvar Alterações da Partida"):
                            if new_t1_form_inn and new_t2_form_inn and new_t1_form_inn != new_t2_form_inn:
                                new_dt_iso_val_inn = None
                                if new_dt_form_inn and new_tm_form_inn: new_dt_iso_val_inn = datetime.combine(new_dt_form_inn, new_tm_form_inn).isoformat()
                                elif new_dt_form_inn: new_dt_iso_val_inn = datetime.combine(new_dt_form_inn, datetime.min.time()).isoformat()
                                
                                st.session_state.matches[original_match_idx_manage].update({
                                    'team1': new_t1_form_inn, 'team2': new_t2_form_inn, 
                                    'format': new_fmt_form_inn, 'datetime_iso': new_dt_iso_val_inn, 
                                    'group': new_grp_form_inn
                                })
                                save_data(MATCHES_BASENAME, st.session_state.matches, championship_id=championship_id)
                                st.success("Alterações salvas."); st.rerun()
                            else: st.error("Times inválidos para alteração.")
                
                st.markdown(f"**Registrar/Editar Resultado**")
                with st.form(key=f"result_match_form_inn_{match_id_disp}_{championship_id}"): # Renomeado
                    res_cols_scores_form_inn = st.columns(2) # Renomeado
                    val_s1_res_inn = current_match_data_manage.get('result_team1_score') # Renomeado
                    val_s2_res_inn = current_match_data_manage.get('result_team2_score') # Renomeado
                    initial_s1_res_inn = 0 if val_s1_res_inn is None else val_s1_res_inn # Renomeado
                    initial_s2_res_inn = 0 if val_s2_res_inn is None else val_s2_res_inn # Renomeado
                    
                    score1_input_res_inn = res_cols_scores_form_inn[0].number_input(f"Placar {current_match_data_manage.get('team1','T1?')}", min_value=0, step=1, value=initial_s1_res_inn, key=f"res_s1_form_inn_{match_id_disp}_{championship_id}") # Renomeado
                    score2_input_res_inn = res_cols_scores_form_inn[1].number_input(f"Placar {current_match_data_manage.get('team2','T2?')}", min_value=0, step=1, value=initial_s2_res_inn, key=f"res_s2_form_inn_{match_id_disp}_{championship_id}") # Renomeado

                    if st.form_submit_button("Salvar Resultado e Calcular Pontos"):
                        valid_score_res_inn = True; fmt_res_inn = current_match_data_manage.get('format') # Renomeado
                        if fmt_res_inn == "MD1" and not ((score1_input_res_inn == 1 and score2_input_res_inn == 0) or (score1_input_res_inn == 0 and score2_input_res_inn == 1)): valid_score_res_inn = False
                        elif fmt_res_inn == "MD3" and not (((score1_input_res_inn == 2 and score2_input_res_inn in [0,1]) or (score2_input_res_inn == 2 and score1_input_res_inn in [0,1])) and score1_input_res_inn != score2_input_res_inn): valid_score_res_inn = False
                        elif fmt_res_inn == "MD5" and not (((score1_input_res_inn == 3 and score2_input_res_inn in [0,1,2]) or (score2_input_res_inn == 3 and score1_input_res_inn in [0,1,2])) and score1_input_res_inn != score2_input_res_inn): valid_score_res_inn = False
                        if score1_input_res_inn == score2_input_res_inn and valid_score_res_inn: valid_score_res_inn = False; st.error("Empates não são permitidos.")
                        if not valid_score_res_inn: st.error("Placar inválido para o formato da partida.")
                        
                        if valid_score_res_inn:
                            st.session_state.matches[original_match_idx_manage].update({
                                'result_team1_score': score1_input_res_inn, 'result_team2_score': score2_input_res_inn, 'status': "Finalizada",
                                'winning_team': current_match_data_manage.get('team1') if score1_input_res_inn > score2_input_res_inn else current_match_data_manage.get('team2')
                            })
                            calculate_points_for_match(match_id_disp, championship_id)
                            save_data(MATCHES_BASENAME, st.session_state.matches, championship_id=championship_id)
                            save_data(BETS_BASENAME, st.session_state.bets, championship_id=championship_id) 
                            st.success("Resultado salvo e pontos calculados!"); st.rerun()
                
                if st.button(f"Excluir Partida ID {match_id_disp}", type="primary", key=f"delete_match_btn_main_{match_id_disp}_{championship_id}"): # Chave única
                    current_bets_delete = st.session_state.get("bets",[]) # Renomeado
                    st.session_state.bets = [b for b in current_bets_delete if b.get('match_id') != match_id_disp]
                    st.session_state.matches.pop(original_match_idx_manage)
                    save_data(MATCHES_BASENAME, st.session_state.matches, championship_id=championship_id)
                    save_data(BETS_BASENAME, st.session_state.bets, championship_id=championship_id)
                    st.warning("Partida e apostas associadas excluídas."); st.rerun()

# --- FIM DO ARQUIVO: admin_views/matches.py ---