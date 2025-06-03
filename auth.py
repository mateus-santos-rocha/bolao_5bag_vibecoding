# Arquivo: auth.py
# Descrição: Funções relacionadas à autenticação de usuários.

import streamlit as st
import hashlib
from data_utils import save_data 
from constants import USERS_BASENAME # CORRIGIDO AQUI

def hash_password(password):
    """Gera um hash SHA256 para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """Renderiza a página de login e registro."""
    st.header("Login do Bolão do Mundial de LoL")
    
    with st.form("login_form"):
        username = st.text_input("Nome de Usuário", key="login_username_auth") 
        password = st.text_input("Senha (apenas para admin)", type="password", key="login_password_auth") 
        submitted = st.form_submit_button("Login")

        if submitted:
            users = st.session_state.get("users", {})
            app_config = st.session_state.get("app_config", {})

            if username in users:
                user_data = users[username]
                if user_data.get("is_admin", False):
                    admin_password_hash_to_check = app_config.get("admin_password_hash")
                    if admin_password_hash_to_check and hash_password(password) == admin_password_hash_to_check:
                        st.session_state.logged_in_user = username
                        st.session_state.is_admin = True
                        st.session_state.page = "Gerenciar Campeonatos" 
                        st.rerun()
                    else:
                        st.error("Senha de admin incorreta.")
                else: 
                    st.session_state.logged_in_user = username
                    st.session_state.is_admin = False
                    st.session_state.page = "Fazer Apostas"
                    st.rerun()
            else:
                st.error("Usuário não encontrado.")

    st.markdown("---")
    st.subheader("Não tem conta? Registre-se aqui (Jogadores)")
    with st.form("register_form"):
        new_username = st.text_input("Escolha um Nome de Usuário para Jogador", key="reg_username_auth")
        reg_submitted = st.form_submit_button("Registrar")

        if reg_submitted:
            if new_username:
                users_reg = st.session_state.get("users", {}) 
                if new_username.lower() == "admin":
                    st.error("Nome de usuário 'admin' é reservado.")
                elif new_username in users_reg:
                    st.error("Este nome de usuário já existe.")
                else:
                    users_reg[new_username] = {"password_hash": None, "is_admin": False}
                    st.session_state.users = users_reg 
                    save_data(USERS_BASENAME, users_reg) # CORRIGIDO AQUI (usa USERS_BASENAME, championship_id é None por padrão)
                    st.success(f"Usuário '{new_username}' registrado com sucesso! Faça o login.")
            else:
                st.warning("Por favor, insira um nome de usuário para registrar.")

# --- FIM DO ARQUIVO: auth.py ---