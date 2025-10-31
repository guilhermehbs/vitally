import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.dataframe_utils import make_dataframe
from src.utils.streamlit_utils import rerun_app
from src.utils.user_utils import get_fisioterapeutas


def render_list_fisioterapeutas_tab(service: ClinicaService) -> None:
    st.subheader("Cadastro de Fisioterapeutas")
    with st.form("form_add_fisio"):
        nome = st.text_input("Nome").strip()
        email = st.text_input("E-mail (opcional)").strip()
        ok = st.form_submit_button("Cadastrar")
    if ok:
        if not nome:
            st.error("Informe o nome.")
        else:
            service.criar_fisioterapeuta(nome, email or None)
            st.success("Fisioterapeuta cadastrado.")
            rerun_app()

    st.divider()
    st.markdown("### Ativos")
    fisios = get_fisioterapeutas(service)
    st.dataframe(
        make_dataframe({"Id": f.id, "Nome": f.nome, "E-mail": f.email} for f in fisios),
        use_container_width=True,
        hide_index=True,
    )
