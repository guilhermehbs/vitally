import logging

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.dataframe_utils import make_dataframe
from src.utils.date_utils import format_date_br

logger = logging.getLogger("vitally_app")


def render_proximos_pagamentos_tab(service: ClinicaService) -> None:
    st.subheader("Vencimentos proximos")
    logger.info("Aba de vencimentos carregada")

    try:
        vencendo = service.vencimentos_proximos()
        logger.info("Total com vencimento próximo: %d", len(vencendo))
    except Exception as exc:
        st.error(f"Erro ao carregar vencimentos: {exc}")
        logger.error("Erro ao carregar vencimentos: %s", exc, exc_info=True)
        return

    if not vencendo:
        st.info("Sem vencimentos proximos.")
        return

    rows = (
        {
            "Id": p.id,
            "Nome": p.nome,
            "Email": p.email,
            "Telefone": p.telefone,
            "Vencimento": format_date_br(p.data_proxima_cobranca),
        }
        for p in vencendo
    )

    df = make_dataframe(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
