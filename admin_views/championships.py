# Arquivo: admin_views/championships.py
# Descrição: Página de gerenciamento de campeonatos.

import streamlit as st
import re
from data_utils import save_data, load_data # load_data para recarregar antes de modificar
from constants import CHAMPIONSHIPS_BASENAME, CHAMPIONSHIP_SETTINGS_BASENAME, DEFAULT_CHAMPIONSHIP_SETTINGS

def slugify(text):
    """Gera um ID amigável (slug) a partir de um texto."""
    if not isinstance(text, str): 
        return "invalid_id"
    text = text.lower()
    text = re.sub(r'\s+', '_', text) 
    text = re.sub(r'[^\w-]', '', text) 
    return text if text else "unnamed_id"

def admin_manage_championships_page():
    """Página para o admin criar, listar e selecionar campeonatos."""
    st.subheader("Gerenciar Campeonatos")

    with st.expander("Criar Novo Campeonato"):
        with st.form("create_championship_form"):
            champ_name = st.text_input("Nome do Novo Campeonato (ex: MSI 2025)")
            create_champ_submitted = st.form_submit_button("Criar Campeonato")

            if create_champ_submitted:
                if champ_name and champ_name.strip():
                    champ_id = slugify(champ_name)
                    championships = st.session_state.get("championships", [])
                    if any(c.get('id') == champ_id for c in championships):
                        st.error(f"Já existe um campeonato com o ID '{champ_id}' (gerado de '{champ_name}'). Escolha um nome diferente.")
                    else:
                        for c_item in championships: # Garante que apenas um seja ativo
                            if isinstance(c_item, dict):
                                c_item['is_active_for_players'] = False
                        
                        new_champ = {"id": champ_id, "name": champ_name.strip(), "is_active_for_players": not bool(championships)}
                        championships.append(new_champ)
                        st.session_state.championships = championships
                        save_data(CHAMPIONSHIPS_BASENAME, championships) 
                        save_data(CHAMPIONSHIP_SETTINGS_BASENAME, DEFAULT_CHAMPIONSHIP_SETTINGS.copy(), championship_id=champ_id)
                        st.success(f"Campeonato '{champ_name.strip()}' (ID: {champ_id}) criado com sucesso!")
                        st.rerun()
                else:
                    st.warning("Por favor, insira um nome para o campeonato.")
    
    st.markdown("---")
    st.write("Campeonatos Existentes:")
    championships_list_display = st.session_state.get("championships", [])
    if not championships_list_display:
        st.info("Nenhum campeonato criado ainda.")
    else:
        for i, champ_display in enumerate(championships_list_display):
            if not isinstance(champ_display, dict):
                st.warning(f"Item inválido na lista de campeonatos: {champ_display}")
                continue

            champ_id_loop_display = champ_display.get('id', f'no_id_{i}')
            champ_name_loop_display = champ_display.get('name', 'Campeonato Sem Nome')
            is_live_display = champ_display.get("is_active_for_players", False)
            
            status_text_display = "🔴 Inativo para Jogadores"
            if is_live_display:
                status_text_display = "🟢 Ativo para Jogadores"

            cols_display = st.columns([3, 2, 2])
            with cols_display[0]:
                st.write(f"**{champ_name_loop_display}** (ID: `{champ_id_loop_display}`)")
                st.caption(status_text_display)
            
            with cols_display[1]:
                if st.button("Selecionar p/ Gerenciar", key=f"select_champ_{champ_id_loop_display}_{i}"):
                    st.session_state.admin_selected_championship_id = champ_id_loop_display
                    st.session_state.page = "Dashboard Admin" 
                    keys_to_del_on_select = ['teams', 'matches', 'bets', 'championship_settings', 'late_bet_requests', 'loaded_for_championship_id']
                    for key_del in keys_to_del_on_select:
                        if key_del in st.session_state:
                            del st.session_state[key_del]
                    st.success(f"Campeonato '{champ_name_loop_display}' selecionado para gerenciamento.")
                    st.rerun() 
            
            with cols_display[2]:
                if not is_live_display:
                    if st.button("Tornar Ativo para Jogadores", key=f"make_live_{champ_id_loop_display}_{i}"):
                        # Recarregar championships do arquivo para evitar condição de corrida com st.session_state
                        current_championships_from_file = load_data(CHAMPIONSHIPS_BASENAME, default_data_factory=lambda: [])
                        updated_championships_live = []
                        
                        made_one_live = False
                        for c_item_live in current_championships_from_file:
                            if isinstance(c_item_live, dict):
                                if c_item_live.get('id') == champ_id_loop_display:
                                    c_item_live['is_active_for_players'] = True
                                    made_one_live = True
                                else:
                                    c_item_live['is_active_for_players'] = False # Garante que apenas um seja ativo
                                updated_championships_live.append(c_item_live)
                        
                        if not made_one_live and champ_id_loop_display not in [c.get('id') for c in updated_championships_live if isinstance(c,dict)]:
                             # Caso o campeonato selecionado não estivesse na lista recarregada (raro, mas por segurança)
                             # Adiciona-o e o torna ativo, desativando outros.
                             for c_item_live in updated_championships_live: c_item_live['is_active_for_players'] = False # Reseta todos
                             updated_championships_live.append({'id': champ_id_loop_display, 'name': champ_name_loop_display, 'is_active_for_players': True})


                        st.session_state.championships = updated_championships_live
                        save_data(CHAMPIONSHIPS_BASENAME, updated_championships_live)
                        
                        st.session_state.live_championship_id = champ_id_loop_display 
                        st.session_state.live_championship_name = champ_name_loop_display
                        st.success(f"Campeonato '{champ_name_loop_display}' agora está ATIVO para jogadores.")
                        st.rerun()
                else:
                    st.markdown("✅ *Ativo para jogadores*")
            st.markdown("---")

# --- FIM DO ARQUIVO: admin_views/championships.py ---