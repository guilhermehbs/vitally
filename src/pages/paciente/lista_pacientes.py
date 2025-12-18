import logging

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.date_utils import format_date_br
from src.utils.streamlit_utils import rerun_app

logger = logging.getLogger("vitally_app")


def render_list_pacientes_tab(service: ClinicaService) -> None:
    st.subheader("Lista de pacientes")

    busca = (
        st.text_input(
            "Buscar por nome ou email",
            placeholder="Digite o nome ou email",
            key="search_paciente",
        )
        .strip()
        .lower()
    )

    only_active = st.checkbox("Somente ativos", value=True, key="chk_only_active")
    logger.info(
        "Listando pacientes (somente_ativos=%s, busca='%s')",
        only_active,
        busca,
    )

    try:
        pacientes = service.listar_pacientes(only_active=only_active)
        logger.info("Total retornado: %d", len(pacientes))
    except Exception as exc:
        st.error(f"Erro ao listar pacientes: {exc}")
        logger.error("Erro ao listar pacientes", exc_info=True)
        return

    if busca:
        pacientes = [
            p
            for p in pacientes
            if busca in (p.nome or "").lower() or busca in (p.email or "").lower()
        ]

    if not pacientes:
        st.info("Nenhum paciente encontrado.")
        return

    cols = st.columns([1, 3, 2, 3, 2, 2, 2, 1])
    headers = [
        "ID",
        "Nome",
        "Telefone",
        "Email",
        "Entrada",
        "Últ. Pgto",
        "Próx. Cobrança",
        "🗑️",
    ]

    for col, header in zip(cols, headers, strict=False):
        col.markdown(f"**{header}**")

    st.divider()

    for p in pacientes:
        cols = st.columns([1, 3, 2, 3, 2, 2, 2, 1])

        cols[0].write(p.id)
        cols[1].write(p.nome)
        cols[2].write(p.telefone or "-")
        cols[3].write(p.email or "-")
        cols[4].write(format_date_br(p.data_entrada))
        cols[5].write(format_date_br(p.data_ultimo_pagamento))
        cols[6].write(format_date_br(p.data_proxima_cobranca))

        if cols[7].button("🗑️", key=f"del_paciente_{p.id}"):
            st.session_state["paciente_delete_id"] = p.id
            st.session_state["paciente_delete_nome"] = p.nome

    if "paciente_delete_id" in st.session_state:
        st.warning(f'Confirma inativar o paciente **{st.session_state["paciente_delete_nome"]}**?')

        col1, col2 = st.columns(2)

        if col1.button("❌ Cancelar"):
            st.session_state.pop("paciente_delete_id", None)
            st.session_state.pop("paciente_delete_nome", None)
            rerun_app()

        if col2.button("✅ Confirmar"):
            try:
                service.inativar_paciente(paciente_id=st.session_state["paciente_delete_id"])

                st.success("Paciente inativado com sucesso.")
                st.session_state.pop("paciente_delete_id", None)
                st.session_state.pop("paciente_delete_nome", None)
                rerun_app()

            except Exception as exc:
                st.error(f"Erro ao inativar paciente: {exc}")
                logger.error("Erro ao inativar paciente", exc_info=True)
