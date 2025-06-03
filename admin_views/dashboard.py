# Arquivo: admin_views/dashboard.py
# Descrição: Página do dashboard do administrador.

import streamlit as st
# Não precisa de pandas aqui, a menos que faça tabelas complexas.

def admin_dashboard_page(championship_id, championship_name):
    """Renderiza o dashboard do administrador para o campeonato ativo."""
    st.title(f"Dashboard Admin - Campeonato: {championship_name}")
    st.write(f"Gerenciando dados para o ID do campeonato: `{championship_id}`")
    
    # Métricas específicas do campeonato
    num_teams_champ = len(st.session_state.get("teams", []))
    matches_champ = st.session_state.get("matches", [])
    num_matches_total_champ = len(matches_champ)
    num_matches_pending_champ = len([m for m in matches_champ if m.get('status') == "Agendada"])
    num_matches_finished_champ = len([m for m in matches_champ if m.get('status') == "Finalizada"])
    num_bets_total_champ = len(st.session_state.get("bets", []))

    # Métricas Globais (ex: usuários)
    num_players_global = len([u for u, data in st.session_state.get("users", {}).items() if not data.get("is_admin")])

    cols_global = st.columns(1)
    cols_global[0].metric("Total de Jogadores Registrados (App)", num_players_global)

    st.markdown("---")
    st.subheader(f"Estatísticas do Campeonato: {championship_name}")
    cols_metrics1_champ = st.columns(3)
    cols_metrics1_champ[0].metric("Times no Campeonato", num_teams_champ)
    cols_metrics1_champ[1].metric("Total de Apostas", num_bets_total_champ)
    cols_metrics1_champ[2].metric("Partidas Cadastradas", num_matches_total_champ)
    
    cols_metrics2_champ = st.columns(2)
    cols_metrics2_champ[0].metric("Partidas Pendentes", num_matches_pending_champ)
    cols_metrics2_champ[1].metric("Partidas Finalizadas", num_matches_finished_champ)
    st.info("Use o menu para gerenciar os dados deste campeonato.")

# --- FIM DO ARQUIVO: admin_views/dashboard.py ---