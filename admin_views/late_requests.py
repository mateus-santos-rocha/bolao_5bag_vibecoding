# Arquivo: admin_views/late_requests.py
# Descrição: Página de gerenciamento de solicitações de apostas tardias.

import streamlit as st
import pandas as pd
from datetime import datetime
from data_utils import save_data
from constants import LATE_BET_REQUESTS_BASENAME

def admin_manage_late_requests_page(championship_id, championship_name):
    """Página para gerenciar solicitações de aposta tardia para o campeonato ativo."""
    st.subheader(f"Solicitações de Aposta Tardia - Campeonato: {championship_name}")

    late_requests = st.session_state.get("late_bet_requests", [])
    if not late_requests:
        st.info("Nenhuma solicitação de aposta tardia para este campeonato.")
        return

    pending_requests = [r for r in late_requests if r.get('status') == 'pending']
    pending_requests_sorted = sorted(pending_requests, key=lambda x: x.get('requested_at_iso', ''), reverse=True)
    processed_requests = [r for r in late_requests if r.get('status') != 'pending']

    st.markdown("#### Solicitações Pendentes")
    if not pending_requests_sorted: st.info("Nenhuma solicitação pendente.")
    else:
        for i, req in enumerate(pending_requests_sorted):
            match_info = next((m for m in st.session_state.get("matches",[]) if m.get('id') == req.get('match_id')), None)
            if not match_info: 
                st.warning(f"Partida ID {req.get('match_id')} da solicitação não encontrada. Pulando.")
                continue

            st.markdown(f"**Usuário:** {req.get('user_id')} | **Partida:** ID {req.get('match_id')} ({match_info.get('team1','?')}-{match_info.get('team2','?')})")
            req_at_iso = req.get('requested_at_iso')
            req_at_display = datetime.fromisoformat(req_at_iso).strftime('%d/%m/%y %H:%M') if req_at_iso else "N/A"
            st.caption(f"ID Solicitação: {req.get('request_id')} | Solicitado em: {req_at_display}")
            
            cols_req_btns = st.columns(2)
            req_id_key = req.get('request_id', f"unk_{i}_{championship_id}") 
            if cols_req_btns[0].button("Aprovar", key=f"appr_{req_id_key}"):
                req_idx = next((idx for idx, r_item in enumerate(st.session_state.late_bet_requests) if r_item.get('request_id') == req.get('request_id')), None)
                if req_idx is not None:
                    st.session_state.late_bet_requests[req_idx]['status'] = 'approved'
                    save_data(LATE_BET_REQUESTS_BASENAME, st.session_state.late_bet_requests, championship_id=championship_id)
                    st.success("Solicitação APROVADA."); st.rerun()
            if cols_req_btns[1].button("Negar", key=f"deny_{req_id_key}", type="primary"):
                req_idx = next((idx for idx, r_item in enumerate(st.session_state.late_bet_requests) if r_item.get('request_id') == req.get('request_id')), None)
                if req_idx is not None:
                    st.session_state.late_bet_requests[req_idx]['status'] = 'denied'
                    save_data(LATE_BET_REQUESTS_BASENAME, st.session_state.late_bet_requests, championship_id=championship_id)
                    st.warning("Solicitação NEGADA."); st.rerun()
            st.markdown("---")

    with st.expander("Ver Solicitações Processadas"):
        if not processed_requests: st.info("Nenhuma solicitação processada neste campeonato.")
        else:
            df_processed_list = []
            # Ordenar processadas por data de solicitação (mais recentes primeiro)
            processed_requests_sorted = sorted(processed_requests, key=lambda x: x.get('requested_at_iso', ''), reverse=True)
            for r_proc in processed_requests_sorted:
                match_info_proc = next((m for m in st.session_state.get("matches", []) if m.get('id') == r_proc.get('match_id')), None)
                match_display = f"ID {r_proc.get('match_id')}"
                if match_info_proc:
                    match_display = f"ID {match_info_proc.get('id', '?')} - {match_info_proc.get('team1', '?')} vs {match_info_proc.get('team2', '?')}"

                requested_at_str = "N/A"
                if r_proc.get('requested_at_iso'):
                    try:
                        requested_at_str = datetime.fromisoformat(r_proc.get('requested_at_iso')).strftime('%d/%m/%y %H:%M')
                    except ValueError:
                        pass # Mantém "N/A"

                df_processed_list.append({
                    "Usuário": r_proc.get('user_id', 'Desconhecido'),
                    "Partida": match_display,
                    "Status": r_proc.get('status', 'N/A').capitalize(),
                    "Solicitado em": requested_at_str,
                    "ID Solicitação": r_proc.get('request_id', 'N/A')
                })
            if df_processed_list:
                st.dataframe(pd.DataFrame(df_processed_list), hide_index=True, use_container_width=True)

# --- FIM DO ARQUIVO: admin_views/late_requests.py ---