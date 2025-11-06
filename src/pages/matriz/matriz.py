import logging

import pandas as pd
import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.user_utils import get_paciente_ativos

logger = logging.getLogger("vitally_app")


def render_matriz_me_tab(service: ClinicaService) -> None:
    st.subheader("Mapa de Exercícios (Pilates)")

    aparelhos = ["Solo", "Chair", "Cadillac", "Reformer", "Barrel"]
    segmentos = ["Cervical", "MMSS", "Tronco", "Abdômen", "MMII"]

    st.markdown("**Plano por paciente (selecione por célula M, E ou M/E):**")
    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    pac_opts = {f"[{p.id}] {p.nome}": p for p in ativos}
    escolha_label = st.selectbox("Paciente", list(pac_opts.keys()), key="pilates_paciente_escolha")
    paciente = pac_opts[escolha_label]
    pid = paciente.id

    if "pilates_plan" not in st.session_state:
        st.session_state.pilates_plan = {}

    if pid not in st.session_state.pilates_plan:
        rows = []
        for ap in aparelhos:
            r = {"Aparelho": ap}
            for seg in segmentos:
                r[seg] = ""
            rows.append(r)
        st.session_state.pilates_plan[pid] = pd.DataFrame(rows, columns=["Aparelho", *segmentos])

    plan_df = st.session_state.pilates_plan[pid]

    col_config = {"Aparelho": st.column_config.TextColumn("Aparelho", disabled=True)}
    select_opts = ["", "M", "E", "M/E"]
    for seg in segmentos:
        col_config[seg] = st.column_config.SelectboxColumn(
            f"{seg}",
            options=select_opts,
            required=False,
            help="Selecione M, E ou M/E para este segmento e aparelho.",
        )

    edited = st.data_editor(
        plan_df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
        num_rows="fixed",
        key=f"pilates_editor_{pid}",
    )
    st.session_state.pilates_plan[pid] = edited

    col1, col2 = st.columns([1, 1])
    with col1:
        csv = edited.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar plano (CSV)",
            data=csv,
            file_name=f"plano_pilates_paciente_{pid}_{paciente.nome}.csv",
            mime="text/csv",
            key=f"dl_csv_{pid}",
        )

    with col2:
        resumo = []
        for _, row in edited.iterrows():
            ap = row["Aparelho"]
            for seg in segmentos:
                val = (row.get(seg) or "").strip()
                if val == "M/E":
                    marcacoes = ["M", "E"]
                elif val in ("M", "E"):
                    marcacoes = [val]
                else:
                    marcacoes = []

                if marcacoes:
                    resumo.append({"Aparelho": ap, "Segmento": seg, "Marcado": "/".join(marcacoes)})

        if resumo:
            st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma marcação ativa neste plano.")
