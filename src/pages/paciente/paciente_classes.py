import logging
from datetime import date

import pandas as pd
import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.classes_utils import build_classes_csv, build_classes_ics
from src.utils.user_utils import get_paciente_ativos

logger = logging.getLogger("vitally_app")


def render_paciente_classes_tab(service: ClinicaService) -> None:
    st.subheader("Aulas")
    logger.info("Aba de aulas carregada")

    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    options = {f"[{p.id}] {p.nome}": p for p in ativos}
    escolha_label = st.selectbox("Paciente", list(options.keys()), key="classes_escolha")
    paciente = options[escolha_label]

    cols = []
    vals = []

    for dia_nome, attr in [
        ("Seg", "aula_seg"),
        ("Ter", "aula_ter"),
        ("Qua", "aula_qua"),
        ("Qui", "aula_qui"),
        ("Sex", "aula_sex"),
        ("Sáb", "aula_sab"),
        ("Dom", "aula_dom"),
    ]:
        cols.append(dia_nome)
        vals.append("X" if getattr(paciente, attr, False) else "")

    df = pd.DataFrame([vals], columns=cols, index=[f"[{paciente.id}] {paciente.nome}"])
    st.dataframe(df, use_container_width=True)

    st.markdown("### Exportar plano de aulas")

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        csv_bytes = build_classes_csv(paciente)
        st.download_button(
            label="Baixar CSV (dias de aula)",
            data=csv_bytes,
            file_name=f"plano_aulas_{paciente.id}_{paciente.nome}.csv",
            mime="text/csv",
            key=f"dl_csv_classes_{paciente.id}",
        )

    with col_b:
        ics_bytes = build_classes_ics(
            paciente=paciente,
            start_on=date.today(),
            start_time_str="08:00",
            duration_minutes=60,
            tzid="America/Sao_Paulo",
        )
        st.download_button(
            label="Baixar .ics (calendário semanal)",
            data=ics_bytes,
            file_name=f"plano_aulas_{paciente.id}_{paciente.nome}.ics",
            mime="text/calendar",
            key=f"dl_ics_classes_{paciente.id}",
        )

    with col_c:
        st.caption(
            "• CSV: visão simples dos dias marcados (Sim/Não).  \n"
            "• ICS: evento semanal recorrente com BYDAY (usado "
            "para importar no calendário Google/Outlook)."
        )
