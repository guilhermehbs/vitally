import datetime as dt
import logging
from datetime import date
from time import sleep

import streamlit as st

from src.services.clinica_service import ClinicaService
from src.utils.add_utils import is_valid_email, only_digits, validate_br_phone
from src.utils.streamlit_utils import rerun_app
from src.utils.time_utils import times_between
from src.utils.user_utils import get_fisioterapeutas, get_paciente_ativos

logger = logging.getLogger("vitally_app")

DIAS = [
    ("Segunda", "aula_seg"),
    ("Terça", "aula_ter"),
    ("Quarta", "aula_qua"),
    ("Quinta", "aula_qui"),
    ("Sexta", "aula_sex"),
    ("Sábado", "aula_sab"),
    ("Domingo", "aula_dom"),
]


def render_edit_pacientes_tab(service: ClinicaService) -> None:
    st.subheader("Editar paciente")
    logger.info("Aba de edição carregada")

    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    options = {f"[{p.id}] {p.nome}": p for p in ativos}
    escolha_label = st.selectbox("Paciente", list(options.keys()), key="edit_escolha")

    with st.form("form_edit_paciente", clear_on_submit=False):
        paciente = options[escolha_label]

        pid = paciente.id
        nome = paciente.nome
        email = paciente.email
        telefone = paciente.telefone

        nome = st.text_input("Nome", key="edit_nome", value=nome).strip()
        email = st.text_input("Email", key="edit_email", value=email).strip()
        telefone_raw = st.text_input(
            "Telefone", key="edit_telefone", placeholder="31999999999", value=telefone
        )
        data_entrada = st.date_input(
            "Data de entrada",
            value=paciente.data_entrada or date.today(),
            format="DD/MM/YYYY",
            key="edit_data_entrada",
        )

        dias_selecionados = st.multiselect(
            "Dias de aula",
            [d for d, _ in DIAS],
            default=[d for d, f in DIAS if getattr(paciente, f, False)],
            key="edit_dias",
        )

        weekday_map = {
            "Segunda": 0,
            "Terça": 1,
            "Quarta": 2,
            "Quinta": 3,
            "Sexta": 4,
            "Sábado": 5,
            "Domingo": 6,
        }
        opcoes_horas = times_between(dt.time(8, 0), dt.time(18, 0), step_min=30)
        for dia in dias_selecionados:
            st.session_state.pop(f"time_{dia}", None)

        horarios: list[tuple[int, str]] = []
        for dia_nome in dias_selecionados:
            hora_str = st.selectbox(
                f"Horário em {dia_nome}",
                options=opcoes_horas,
                index=opcoes_horas.index("09:00") if "09:00" in opcoes_horas else 0,
                key=f"time_{dia_nome}_select",
                placeholder="Selecione um horário",
            )
            horarios.append((weekday_map[dia_nome], hora_str))

        fisioterapeutas = get_fisioterapeutas(service)
        if not fisioterapeutas:
            st.info("Cadastre fisioterapeutas primeiro.")
            return

        options_fisio = {f"[{f.id}] {f.nome}": f for f in fisioterapeutas}
        escolha_label = st.selectbox(
            "Fisioterapeuta", list(options_fisio.keys()), key="edit_escolha_fisioterapeuta"
        )

        fisioterapeuta = options_fisio[escolha_label]
        fisioterapeuta_id = fisioterapeuta.id

        submitted = st.form_submit_button("Editar")

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

    dia_kwargs = {}
    for dia_nome, attr in DIAS:
        dia_kwargs[attr] = dia_nome in dias_selecionados

    try:
        paciente, updates = service.editar_paciente(
            paciente_id=int(pid),
            nome=nome,
            email=email,
            telefone=fone_digits,
            data_entrada=data_entrada,
            **dia_kwargs,
        )
        service.definir_aulas_paciente(
            paciente_id=pid,
            aulas=horarios,
            fisioterapeuta_id=fisioterapeuta_id,
            duracao_min=60,
            semanas=4,
        )
        st.success(f"Editado #{paciente.id}")
        for campo, (antes, depois) in updates.items():
            st.success(f'[EDIT] {campo}: "{antes}" → "{depois}"')
        sleep(2)
        rerun_app()
    except Exception as exc:
        st.error(f"Erro ao cadastrar paciente: {exc}")
        logger.error("Erro ao cadastrar paciente: %s", exc, exc_info=True)
