# Arquivo: admin_views/settings.py
# Descrição: Página de configurações de pontos do campeonato.

import streamlit as st
from data_utils import save_data
from constants import CHAMPIONSHIP_SETTINGS_BASENAME, DEFAULT_CHAMPIONSHIP_SETTINGS

def admin_settings_page(championship_id, championship_name):
    """Renderiza a página de configurações de PONTOS do campeonato ativo."""
    st.subheader(f"Configurações de Pontuação - Campeonato: {championship_name}")
    
    current_champ_settings = st.session_state.get("championship_settings", DEFAULT_CHAMPIONSHIP_SETTINGS.copy())
    # Garante que não estamos modificando o default diretamente se current_champ_settings for o default.
    champ_settings_form = current_champ_settings.copy() if current_champ_settings else DEFAULT_CHAMPIONSHIP_SETTINGS.copy()


    champ_settings_form["points_md1"] = st.number_input(
        "Pontos por acertar MD1:", 
        min_value=0, 
        value=int(champ_settings_form.get("points_md1", DEFAULT_CHAMPIONSHIP_SETTINGS["points_md1"]))
    )
    champ_settings_form["points_md3_md5_winner"] = st.number_input(
        "Pontos por acertar vencedor MD3/MD5 (placar errado):", 
        min_value=0, 
        value=int(champ_settings_form.get("points_md3_md5_winner", DEFAULT_CHAMPIONSHIP_SETTINGS["points_md3_md5_winner"]))
    )
    champ_settings_form["points_md3_md5_score"] = st.number_input(
        "Pontos por acertar placar exato MD3/MD5:", 
        min_value=0, 
        value=int(champ_settings_form.get("points_md3_md5_score", DEFAULT_CHAMPIONSHIP_SETTINGS["points_md3_md5_score"]))
    )

    if st.button("Salvar Configurações de Pontuação do Campeonato"):
        st.session_state.championship_settings = champ_settings_form 
        save_data(CHAMPIONSHIP_SETTINGS_BASENAME, champ_settings_form, championship_id=championship_id)
        st.success(f"Configurações de pontuação para o campeonato '{championship_name}' salvas!")
        st.rerun()

# --- FIM DO ARQUIVO: admin_views/settings.py ---