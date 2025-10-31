import streamlit as st


def logout_button() -> None:
    with st.sidebar:
        if st.button("Sair"):
            st.session_state.pop("auth_user", None)
            st.experimental_rerun()


def header_userbar(user: dict):
    st.markdown(
        """
                    <style>
                    .vitally-popover { width: 250px; }
                    .vitally-popover .stMarkdown { margin-bottom: .25rem; }
                    .vitally-popover hr { margin: .25rem 0; }
                    </style>
                """,
        unsafe_allow_html=True,
    )
    _, col_user = st.columns([0.85, 0.15], vertical_alignment="center")
    with col_user:
        try:
            with st.popover(f"👤 {user['name']}"):
                st.markdown("<div class='vitally-popover'>", unsafe_allow_html=True)
                st.caption(user["email"])
                st.divider()
                if st.button("Sair", key="logout_small"):
                    st.session_state.pop("auth_user", None)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.markdown(
                f"<div style='text-align:right;'>👤 <b>{user['name']}</b></div>",
                unsafe_allow_html=True,
            )
            if st.button("Sair", key="logout_top", use_container_width=True):
                st.session_state.pop("auth_user", None)
                st.rerun()
