import streamlit as st

from src.security.auth import get_user_by_email, verify_password


def ensure_auth() -> bool:
    if st.session_state.get("auth_user"):
        return True

    st.title("🩺 Vitally")
    st.subheader("Entrar")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("E-mail").strip()
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if not email or not password:
            st.error("Informe e-mail e senha.")
            return False

        user = get_user_by_email(email)
        if not user:
            st.error("Usuário não encontrado ou inativo.")
            return False

        if not verify_password(password, user.password_hash):
            st.error("Senha inválida.")
            return False

        st.session_state.auth_user = {"id": user.id, "name": user.name, "email": user.email}
        st.success(f"Bem-vindo(a), {user.name}!")
        st.rerun()

    return False
