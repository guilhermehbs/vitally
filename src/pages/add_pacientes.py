import logging
from datetime import date
from time import sleep

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.add_utils import is_valid_email, only_digits, validate_br_phone
from src.utils.date_utils import format_date_br
from src.utils.streamlit_utils import rerun_app

logger = logging.getLogger("vitally_app")


def render_add_pacientes_tab(service: ClinicaService) -> None:
    st.subheader("Cadastrar paciente")
    logger.info("Aba de cadastro carregada")

    if "add_tel_mask" not in st.session_state:
        st.session_state.add_tel_mask = ""
    if "add_tel_digits" not in st.session_state:
        st.session_state.add_tel_digits = ""

    with st.form("form_add_paciente", clear_on_submit=False):
        nome = st.text_input("Nome", key="add_nome").strip()
        email = st.text_input("E-mail", key="add_email").strip()
        telefone_raw = st.text_input("Telefone", key="add_telefone", placeholder="31999999999")
        data_entrada = st.date_input(
            "Data de entrada",
            value=date.today(),
            format="DD/MM/YYYY",
            key="add_data_entrada",
        )
        submitted = st.form_submit_button("Cadastrar")

    if not submitted:
        return

    if not nome:
        st.error("Informe o nome")
        return

    if email and not is_valid_email(email):
        st.error("Email inválido")
        return

    fone_digits = only_digits(telefone_raw)
    ok, msg = validate_br_phone(fone_digits)
    if not ok:
        st.error(msg or "Telefone inválido. Digite DDD + número (ex.: 3199XXXXXXX ou 3130XXXXXX)")
        return

    if data_entrada > date.today():
        st.error("Data de entrada não pode ser futura")
        return

    try:
        paciente = service.cadastrar_paciente(
            nome=nome,
            email=email,
            telefone=fone_digits,
            data_entrada=data_entrada,
        )
        prox = format_date_br(paciente.data_proxima_cobranca)
        st.success(
            f"""Cadastrado #{paciente.id}, Nome: {paciente.nome}, 
            Email: {paciente.email}, Telefone: {paciente.telefone}, 
            Entrada: {format_date_br(paciente.data_entrada)}, 
            Próxima cobrança: {prox}"""
        )
        sleep(2)
        rerun_app()
    except Exception as exc:
        st.error(f"Erro ao cadastrar paciente: {exc}")
        logger.error("Erro ao cadastrar paciente: %s", exc, exc_info=True)
