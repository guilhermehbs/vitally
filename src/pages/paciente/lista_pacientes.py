import logging

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.dataframe_utils import make_dataframe
from src.utils.date_utils import format_date_br
from src.utils.user_utils import get_paciente_ativos

logger = logging.getLogger("vitally_app")


def render_list_pacientes_tab(service: ClinicaService) -> None:
    st.subheader("Lista de pacientes")
    only_active = st.checkbox("Somente ativos", value=True, key="chk_only_active")
    logger.info("Listando pacientes (somente_ativos=%s)", only_active)

    try:
        pacientes = get_paciente_ativos(service)
        logger.info("Total retornado: %d", len(pacientes))
    except Exception as exc:
        st.error(f"Erro ao listar pacientes: {exc}")
        logger.error("Erro ao listar pacientes: %s", exc, exc_info=True)
        return

    if not pacientes:
        st.info("Nenhum paciente.")
        return

    rows = (
        {
            "Id": p.id,
            "Nome": p.nome,
            "Telefone": p.telefone,
            "Email": p.email,
            "Entrada": format_date_br(p.data_entrada),
            "Último pagamento": format_date_br(p.data_ultimo_pagamento),
            "Próxima cobrança": format_date_br(p.data_proxima_cobranca),
            "Ativo": p.ativo,
        }
        for p in pacientes
    )

    df = make_dataframe(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
