# Arquivo: logic.py
# Descrição: Contém a lógica de negócios do aplicativo, como cálculo de pontos.

import streamlit as st 

def calculate_points_for_match(match_id, championship_id):
    """Calcula pontos para uma partida finalizada, usando as config de pontos do campeonato."""
    if 'matches' not in st.session_state or 'championship_settings' not in st.session_state or 'bets' not in st.session_state:
        st.error("Erro: Dados do campeonato não carregados para calcular pontos.")
        return

    match_obj = next((m for m in st.session_state.matches if m.get('id') == match_id and m.get('status') == "Finalizada"), None)
    if not match_obj:
        return

    championship_settings = st.session_state.get("championship_settings", {})
    actual_winner = match_obj.get('winning_team')
    actual_score1 = match_obj.get('result_team1_score')
    actual_score2 = match_obj.get('result_team2_score')

    for bet_idx, bet in enumerate(st.session_state.bets):
        if bet.get('match_id') == match_id: 
            points = 0
            predicted_winner = bet.get('predicted_winner')
            predicted_score1 = bet.get('predicted_score1')
            predicted_score2 = bet.get('predicted_score2')

            correct_winner_guess = (predicted_winner == actual_winner)

            if match_obj.get('format') == "MD1":
                if correct_winner_guess:
                    points = championship_settings.get("points_md1", 2) 
            else: 
                correct_score_guess = (predicted_score1 == actual_score1 and predicted_score2 == actual_score2)
                if correct_winner_guess and correct_score_guess:
                    points = championship_settings.get("points_md3_md5_score", 5)
                elif correct_winner_guess: 
                    points = championship_settings.get("points_md3_md5_winner", 1)
            
            st.session_state.bets[bet_idx]['points_awarded'] = points

# --- FIM DO ARQUIVO: logic.py ---