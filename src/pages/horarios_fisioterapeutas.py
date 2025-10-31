from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.classes_utils import build_times_csv, build_times_ics
from src.utils.user_utils import get_fisioterapeutas


def render_fisioterapeutas_horarios_tab(service: ClinicaService) -> None:
    st.subheader("Grade do Fisioterapeuta")

    fisios = get_fisioterapeutas(service)
    if not fisios:
        st.info("Cadastre um fisioterapeuta")
        return

    options = {f"[{f.id}] {f.nome}": f for f in fisios}
    escolha = st.selectbox("Fisioterapeuta", list(options.keys()), key="grade_fisio_escolha")
    fisio = options[escolha]

    col1, col2 = st.columns([1, 1])
    with col1:
        semana_ini = st.date_input("Início da semana", value=date.today())
    with col2:
        slot_min = st.number_input("Tamanho do slot (min)", value=30, min_value=15, step=15)

    data_fim = semana_ini + timedelta(days=6)
    itens = service.grade_do_fisio(fisio.id, semana_ini, data_fim)

    try:
        todos = service.listar_pacientes(only_active=False)
        nome_by_id = {p.id: p.nome for p in todos}
    except Exception:
        nome_by_id = {}

    dias = [semana_ini + timedelta(days=i) for i in range(7)]
    horas = []

    dia_start = time(8, 0)
    dia_end = time(18, 0)
    cur = datetime.combine(semana_ini, dia_start)
    end = datetime.combine(semana_ini, dia_end)
    while cur.time() <= end.time():
        horas.append(cur.time().strftime("%H:%M"))
        cur += timedelta(minutes=slot_min)

    grid = {h: {d.strftime("%a %d/%m"): "" for d in dias} for h in horas}

    for ag in itens:
        chave_col = ag.data.strftime("%a %d/%m")
        chave_linha = ag.hora_inicio.strftime("%H:%M")

        if chave_linha < "09:00" or chave_linha > "18:00":
            continue

        nome = ""
        if ag.paciente_id:
            nome = nome_by_id.get(ag.paciente_id, f"#{ag.paciente_id}")

        grid.setdefault(chave_linha, {})[chave_col] = nome or "Livre"

    df = pd.DataFrame.from_dict(grid, orient="index")[list(grid[horas[0]].keys())]

    st.dataframe(df, use_container_width=True, height=773)

    st.markdown("### Exportar horários do fisioterapeuta")

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        csv_bytes = build_times_csv(fisio)
        st.download_button(
            label="Baixar CSV (horários)",
            data=csv_bytes,
            file_name=f"horarios_fisio_{fisio.id}_{fisio.nome}.csv",
            mime="text/csv",
            key=f"dl_csv_horarios_{fisio.id}",
        )

    with col_b:
        ics_bytes = build_times_ics(
            fisio=fisio,
            start_on=date.today(),
            start_time_str="08:00",
            duration_minutes=30,
            tzid="America/Sao_Paulo",
        )
        st.download_button(
            label="Baixar .ics (calendário semanal)",
            data=ics_bytes,
            file_name=f"horarios_fisio_{fisio.id}_{fisio.nome}.ics",
            mime="text/calendar",
            key=f"dl_ics_times_{fisio.id}",
        )

    with col_c:
        st.caption(
            "• CSV: visão simples dos dias marcados (Sim/Não).  \n"
            "• ICS: evento semanal recorrente com BYDAY (usado "
            "para importar no calendário Google/Outlook)."
        )
