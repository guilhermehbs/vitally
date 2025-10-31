import datetime as dt

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.time_utils import times_between
from src.utils.user_utils import get_fisioterapeutas


def render_fisioterapeutas_disponibilidade_tab(service: ClinicaService) -> None:
    st.subheader("Disponibilidade do Fisioterapeuta")

    fisios = get_fisioterapeutas(service)
    if not fisios:
        st.info("Cadastre um fisioterapeuta")
        return

    options = {f"[{f.id}] {f.nome}": f for f in fisios}
    escolha = st.selectbox("Fisioterapeuta", list(options.keys()))
    fisio = options[escolha]

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    weekday_map = {d: i for i, d in enumerate(dias)}

    opcoes_horas = times_between(dt.time(8, 0), dt.time(18, 0), step_min=30)

    for d in dias:
        st.session_state.pop(f"ini_{d}", None)
        st.session_state.pop(f"fim_{d}", None)

    rows: list[tuple[int, str, str]] = []
    with st.form("form_dispon"):
        st.caption(
            "Preencha as janelas (deixe desmarcado para não definir disponibilidade naquele dia)"
        )
        erros: list[str] = []

        for d in dias:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                on = st.checkbox(d, key=f"chk_{d}")
            with c2:
                h1 = st.selectbox(
                    "Início",
                    options=opcoes_horas,
                    index=opcoes_horas.index("09:00") if "09:00" in opcoes_horas else 0,
                    key=f"ini_{d}_sel",
                    disabled=not on,
                )
            with c3:
                h2 = st.selectbox(
                    "Fim",
                    options=opcoes_horas,
                    index=(
                        opcoes_horas.index("17:00")
                        if "17:00" in opcoes_horas
                        else len(opcoes_horas) - 1
                    ),
                    key=f"fim_{d}_sel",
                    disabled=not on,
                )

            if on:
                if h2 <= h1:
                    try:
                        base = dt.datetime.strptime(h1, "%H:%M")
                        sugestao = (base + dt.timedelta(minutes=30)).strftime("%H:%M")
                    except Exception:
                        sugestao = "próximo horário"
                    erros.append(
                        f"{d}: horário final deve ser maior que o inicial (ex.: {h1}–{sugestao})."
                    )
                else:
                    rows.append((weekday_map[d], h1, h2))

        ok = st.form_submit_button("Salvar disponibilidades")

    if ok:
        if erros:
            for e in erros:
                st.error(e)
            st.stop()

        service.definir_disponibilidades_fisio(fisio.id, rows)
        st.success("Disponibilidades salvas.")
        if rows:
            st.write("**Resumo:**")
            for wd, i, f in rows:
                st.write(f"- {dias[wd]}: {i}–{f}")
        else:
            st.info(
                "Nenhum dia selecionado; o fisioterapeuta ficará sem disponibilidades cadastradas."
            )
