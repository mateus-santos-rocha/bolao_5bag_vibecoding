# Arquivo: player_pages.py
# Descrição: Funções que renderizam as páginas da seção do jogador.
# (Este arquivo foi ATUALIZADO para a nova lógica de apostas)

import streamlit as st
import pandas as pd
from datetime import datetime
from data_utils import save_data
from constants import BETS_BASENAME, LATE_BET_REQUESTS_BASENAME 

def player_make_bets_page(championship_id, championship_name):
    st.subheader(f"Fazer Apostas - Campeonato: {championship_name}")
    
    if championship_id is None:
        st.warning("Nenhum campeonato ativo para apostas. Contate o administrador.")
        return

    current_time = datetime.now() 
    user_id = st.session_state.logged_in_user
    
    current_matches_player = st.session_state.get("matches", []) 
    late_requests_player = st.session_state.get("late_bet_requests", []) 
    current_bets_player = st.session_state.get("bets", []) 

    all_scheduled_matches_player = [m for m in current_matches_player if m.get('status') == "Agendada"]
    
    if not all_scheduled_matches_player:
        st.info("Nenhuma partida agendada para apostas neste campeonato.")
        return

    all_scheduled_matches_sorted_player = sorted(all_scheduled_matches_player, key=lambda x: (x.get('datetime_iso') or 'zzzzzzzz', x.get('id', 0)))

    for i, match_player in enumerate(all_scheduled_matches_sorted_player):
        match_id_player = match_player.get('id', f"match_idx_{i}_{championship_id}") 
        st.markdown("---")
        dt_display_player = "Não definida"; is_past_deadline_player = False
        if match_player.get('datetime_iso'):
            try:
                match_dt_obj = datetime.fromisoformat(match_player['datetime_iso'])
                dt_display_player = match_dt_obj.strftime('%d/%m/%Y %H:%M')
                current_time_comp = datetime.now(match_dt_obj.tzinfo) if match_dt_obj.tzinfo else datetime.now()
                if current_time_comp >= match_dt_obj: is_past_deadline_player = True
            except ValueError: dt_display_player = f"Data Inválida ({match_player.get('datetime_iso')})"
        
        st.markdown(f"**ID {match_id_player}: {match_player.get('team1','?')} vs {match_player.get('team2','?')}** ({match_player.get('format','?')})")
        st.caption(f"Grupo: *{match_player.get('group','N/A')}* | Prazo: {dt_display_player}")

        approved_late_player = False; existing_req_status_player = None
        req_id_player_key = f"{user_id}_{match_id_player}" 

        for req in late_requests_player:
            if req.get('request_id') == req_id_player_key:
                existing_req_status_player = req.get('status')
                if req.get('status') == 'approved': approved_late_player = True
                break
        
        is_bettable_player = (not is_past_deadline_player) or (is_past_deadline_player and approved_late_player)

        if is_bettable_player:
            user_bet = next((b for b in current_bets_player if b.get('user_id') == user_id and b.get('match_id') == match_id_player), None)
            
            # Carregar placares existentes para o formulário
            default_score1_val = user_bet.get('predicted_score1', 0) if user_bet else 0
            default_score2_val = user_bet.get('predicted_score2', 0) if user_bet else 0
            
            form_key_bet = f"bet_form_{match_id_player}_{user_id}_{championship_id}_{i}"
            match_format_val = match_player.get('format')

            with st.form(key=form_key_bet):
                predicted_winner_for_md1 = None # Só usado para MD1

                if match_format_val == "MD1":
                    winner_options = [match_player.get('team1','?'), match_player.get('team2','?')]
                    winner_options = [opt for opt in winner_options if opt and opt != '?']
                    default_winner_md1 = user_bet.get('predicted_winner') if user_bet and user_bet.get('predicted_winner') in winner_options else (winner_options[0] if winner_options else None)
                    winner_idx_md1 = winner_options.index(default_winner_md1) if default_winner_md1 and default_winner_md1 in winner_options else 0
                    
                    if winner_options: # Só mostra radio se houver opções
                        predicted_winner_for_md1 = st.radio("Vencedor Previsto (MD1):", winner_options, index=winner_idx_md1, key=f"winner_md1_{form_key_bet}", horizontal=True)
                    else:
                        st.error("Times não definidos para MD1.")

                # Inputs de placar para MD3/MD5 (e também para MD1, mas serão 1 ou 0 e o vencedor será pego do radio)
                # Para MD3/MD5, estes são os únicos inputs para determinar o vencedor.
                st.write("Placar Previsto:" if match_format_val != "MD1" else "Placar (MD1 é 1-0 ou 0-1):")
                cols_s_form = st.columns(2)
                max_s_val_form = 1 if match_format_val == "MD1" else (2 if match_format_val == "MD3" else 3)
                
                # Se MD1, os campos de placar são mais para confirmação visual ou não são editáveis diretamente aqui.
                # O placar de MD1 será derivado do vencedor selecionado.
                # Para MD3/MD5, estes são os inputs primários.

                pred_s1_form = cols_s_form[0].number_input(f"{match_player.get('team1','?')}", min_value=0, max_value=max_s_val_form, step=1, 
                                                           value=int(default_score1_val), key=f"pscore1_{form_key_bet}",
                                                           disabled=(match_format_val == "MD1")) # Desabilitar para MD1 se preferir
                pred_s2_form = cols_s_form[1].number_input(f"{match_player.get('team2','?')}", min_value=0, max_value=max_s_val_form, step=1, 
                                                           value=int(default_score2_val), key=f"pscore2_{form_key_bet}",
                                                           disabled=(match_format_val == "MD1")) # Desabilitar para MD1 se preferir
                
                bet_btn_label_form = "Atualizar Aposta" if user_bet else "Salvar Aposta"
                if approved_late_player: bet_btn_label_form += " (Tardia Autorizada)"
                submit_bet = st.form_submit_button(bet_btn_label_form)

                if submit_bet:
                    is_valid_sub = True
                    final_predicted_winner = None
                    final_s1, final_s2 = 0, 0

                    if match_format_val == "MD1":
                        if not predicted_winner_for_md1: # Se times não estavam disponíveis
                            st.error("Não foi possível determinar o vencedor para MD1.")
                            is_valid_sub = False
                        else:
                            final_predicted_winner = predicted_winner_for_md1
                            if final_predicted_winner == match_player.get('team1'):
                                final_s1, final_s2 = 1, 0
                            else:
                                final_s1, final_s2 = 0, 1
                            # Validação do placar para MD1 (já implícito pela seleção)
                            if not ((final_s1 == 1 and final_s2 == 0) or (final_s1 == 0 and final_s2 == 1)):
                                st.error("Placar inválido para MD1. Deve ser 1-0 ou 0-1.")
                                is_valid_sub = False
                    
                    else: # MD3 ou MD5 - Derivar vencedor do placar
                        final_s1, final_s2 = pred_s1_form, pred_s2_form
                        if final_s1 > final_s2: final_predicted_winner = match_player.get('team1')
                        elif final_s2 > final_s1: final_predicted_winner = match_player.get('team2')
                        else: # Empate
                            st.error("Empate não é um resultado de placar válido."); is_valid_sub = False
                        
                        # Validação de formato do placar para MD3/MD5
                        if is_valid_sub: # Só valida formato se não houve erro de empate
                            if match_format_val == "MD3" and not (((final_s1 == 2 and final_s2 in [0,1]) or (final_s2 == 2 and final_s1 in [0,1]))):
                                st.error(f"Placar {final_s1}-{final_s2} inválido para MD3 (Ex: 2-0, 2-1, 0-2, 1-2).")
                                is_valid_sub = False
                            elif match_format_val == "MD5" and not (((final_s1 == 3 and final_s2 in [0,1,2]) or (final_s2 == 3 and final_s1 in [0,1,2]))):
                                st.error(f"Placar {final_s1}-{final_s2} inválido para MD5 (Ex: 3-0, 3-1, 3-2, 0-3, 1-3, 2-3).")
                                is_valid_sub = False
                        
                        if is_valid_sub and not final_predicted_winner: # Segurança, caso placar válido não derive vencedor (não deveria acontecer)
                            st.error("Não foi possível determinar o vencedor a partir do placar.")
                            is_valid_sub = False

                    if is_valid_sub and final_predicted_winner:
                        bet_data = {"user_id": user_id, "match_id": match_id_player, 
                                    "predicted_winner": final_predicted_winner, 
                                    "predicted_score1": final_s1, "predicted_score2": final_s2, 
                                    "points_awarded": 0, "is_late_bet": approved_late_player}
                        
                        existing_bet_idx = next((idx for idx, b_item in enumerate(current_bets_player) if b_item.get('user_id') == user_id and b_item.get('match_id') == match_id_player), None)
                        if existing_bet_idx is not None: current_bets_player[existing_bet_idx] = bet_data
                        else: current_bets_player.append(bet_data)
                        
                        st.session_state.bets = current_bets_player 
                        save_data(BETS_BASENAME, current_bets_player, championship_id=championship_id)
                        st.success("Aposta salva/atualizada!"); st.rerun()
        
        elif is_past_deadline_player: # Lógica para solicitar aposta tardia
            if existing_req_status_player == 'pending': st.info(f"Solicitação de aposta tardia PENDENTE para ID {match_id_player}.")
            elif existing_req_status_player == 'denied': st.error(f"Solicitação de aposta tardia NEGADA para ID {match_id_player}.")
            else:
                if st.button("Solicitar Aposta Tardia", key=f"req_late_{match_id_player}_{user_id}_{championship_id}"):
                    existing_req_idx_save = next((idx for idx, r_item in enumerate(late_requests_player) if r_item.get('request_id') == req_id_player_key), None)
                    ts_now_save = datetime.now().isoformat()
                    if existing_req_idx_save is not None:
                        late_requests_player[existing_req_idx_save]['status'] = 'pending'
                        late_requests_player[existing_req_idx_save]['requested_at_iso'] = ts_now_save
                    else:
                        new_req_save = {"request_id": req_id_player_key, "user_id": user_id, "match_id": match_id_player, "status": "pending", "requested_at_iso": ts_now_save}
                        late_requests_player.append(new_req_save)
                    
                    st.session_state.late_bet_requests = late_requests_player 
                    save_data(LATE_BET_REQUESTS_BASENAME, late_requests_player, championship_id=championship_id)
                    st.success(f"Solicitação enviada para ID {match_id_player}."); st.rerun()

def player_my_bets_page(championship_id, championship_name):
    st.subheader(f"Minhas Apostas - Campeonato: {championship_name}")
    if championship_id is None:
        st.warning("Nenhum campeonato ativo. Contate o admin."); return
    user_id_mybet = st.session_state.logged_in_user
    bets_mybet = st.session_state.get("bets", []) 
    matches_mybet = st.session_state.get("matches", []) 
    user_bets_champ = [b for b in bets_mybet if b.get('user_id') == user_id_mybet]
    if not user_bets_champ: st.info("Você não fez apostas neste campeonato."); return
    my_bets_data_display = []
    for bet_disp in sorted(user_bets_champ, key=lambda x: x.get('match_id',0)):
        match_info_disp = next((m for m in matches_mybet if m.get('id') == bet_disp.get('match_id')), None)
        if match_info_disp:
            score_pred = f"{bet_disp.get('predicted_score1','?')}-{bet_disp.get('predicted_score2','?')}"
            # Para MD1, o placar exato da aposta não é tão relevante quanto o vencedor.
            # Mas se foi salvo, pode ser exibido.
            # if match_info_disp.get('format') == "MD1": score_pred = "N/A (MD1)" 
            late_tag = " (Tardia)" if bet_disp.get('is_late_bet') else ""
            points_val = 'Pendente'
            if match_info_disp.get('status') == 'Finalizada':
                points_val = bet_disp.get('points_awarded', 0)
            my_bets_data_display.append({
                "ID Partida": match_info_disp.get('id','?'),
                "Partida": f"{match_info_disp.get('team1','T1?')} vs {match_info_disp.get('team2','T2?')} ({match_info_disp.get('format')})",
                "Meu Vencedor": bet_disp.get('predicted_winner','?'),
                "Meu Placar": score_pred + late_tag,
                "Resultado Real": f"{match_info_disp.get('result_team1_score','?')}x{match_info_disp.get('result_team2_score','?')} (V: {match_info_disp.get('winning_team','?')})" if match_info_disp.get('status') == 'Finalizada' else 'Pendente',
                "Pontos": points_val
            })
    if my_bets_data_display: st.dataframe(pd.DataFrame(my_bets_data_display), hide_index=True, use_container_width=True)
    else: st.info("Nenhuma aposta para exibir.")

# --- FIM DO ARQUIVO: player_pages.py ---