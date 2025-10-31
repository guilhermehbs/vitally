import logging
from datetime import date

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.date_utils import format_date_br
from src.utils.streamlit_utils import rerun_app
from src.utils.user_utils import get_paciente_ativos

logger = logging.getLogger("vitally_app")


def render_pagamentos_tab(service: ClinicaService) -> None:
    st.subheader("Registrar pagamento")
    logger.info("Aba de pagamento carregada")

    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    options = {f"[{p.id}] {p.nome}": p.id for p in ativos}
    escolha_label = st.selectbox("Paciente", list(options.keys()), key="pay_escolha")

    data_pagamento = st.date_input(
        "Data do pagamento", value=date.today(), format="DD/MM/YYYY", key="pay_data"
    )

    if st.button("Registrar", type="primary", key="btn_registrar_pag"):
        pid = options[escolha_label]
        logger.info("Registrando pagamento: paciente_id=%s em %s", pid, data_pagamento)
        try:
            paciente = service.registrar_pagamento(pid, data_pagamento)
            prox = format_date_br(paciente.data_proxima_cobranca)
            st.success(f"Pagamento registrado. Próx. cobrança: {prox}")
            logger.info("Pagamento OK: paciente_id=%s próxima=%s", paciente.id, prox)
            rerun_app()
        except Exception as exc:
            st.error(f"Erro ao registrar pagamento: {exc}")
            logger.error("Erro ao registrar pagamento: %s", exc, exc_info=True)
