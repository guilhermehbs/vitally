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

WEEKDAY_MAP = {
    "Segunda": 0,
    "Terça": 1,
    "Quarta": 2,
    "Quinta": 3,
    "Sexta": 4,
    "Sábado": 5,
    "Domingo": 6,
}


def _build_options(items, labelfn):
    opts = {labelfn(item): item for item in items}
    return list(opts.keys()), opts


def _cleanup_time_state(dias):
    for dia in dias:
        st.session_state.pop(f"time_{dia}_select", None)


def _validar_campos(nome, email, telefone_raw, data_entrada):
    if not nome:
        st.error("Informe o nome")
        return False

    if email and not is_valid_email(email):
        st.error("Email inválido")
        return False

    fone_digits = only_digits(telefone_raw or "")
    ok, msg = validate_br_phone(fone_digits)
    if not ok:
        st.error(msg or "Telefone inválido. Digite DDD + número")
        return False

    if data_entrada > date.today():
        st.error("Data de entrada não pode ser futura")
        return False

    return True


def render_edit_pacientes_tab(service: ClinicaService) -> None:
    st.subheader("Editar paciente")
    logger.info("Aba de edição carregada")

    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    labels_pac, options_pac = _build_options(ativos, lambda p: f"[{p.id}] {p.nome}")

    LABEL_VAZIO = "— Selecione um paciente —"
    labels_pac = [LABEL_VAZIO] + labels_pac

    escolha_label = st.selectbox(
        "Paciente",
        labels_pac,
        index=0,
        key="edit_escolha",
    )

    if escolha_label == LABEL_VAZIO:
        st.info("Selecione um paciente para editar.")
        return

    paciente = options_pac[escolha_label]

    if st.session_state.get("edit_paciente_id") != paciente.id:
        st.session_state["edit_paciente_id"] = paciente.id
        st.session_state["edit_nome"] = paciente.nome
        st.session_state["edit_email"] = paciente.email or ""
        st.session_state["edit_telefone"] = paciente.telefone or ""
        st.session_state["edit_data_entrada"] = paciente.data_entrada or date.today()
        st.session_state["edit_dias"] = [d for d, attr in DIAS if getattr(paciente, attr, False)]

    with st.form("form_edit_paciente", clear_on_submit=False):
        pid = paciente.id

        nome = st.text_input("Nome", key="edit_nome").strip()
        email = st.text_input("Email", key="edit_email").strip()
        telefone_raw = st.text_input(
            "Telefone",
            key="edit_telefone",
            placeholder="31999999999",
        )
        data_entrada = st.date_input(
            "Data de entrada",
            key="edit_data_entrada",
            format="DD/MM/YYYY",
        )

        dias_selecionados = st.multiselect(
            "Dias de aula",
            [d for d, _ in DIAS],
            key="edit_dias",
        )

        _cleanup_time_state(dias_selecionados)
        opcoes_horas = times_between(dt.time(8, 0), dt.time(18, 0), step_min=30)

        horarios: list[tuple[int, str]] = []
        for dia_nome in dias_selecionados:
            hora_str = st.selectbox(
                f"Horário em {dia_nome}",
                options=opcoes_horas,
                key=f"time_{dia_nome}_select",
            )
            horarios.append((WEEKDAY_MAP[dia_nome], hora_str))

        fisioterapeutas = get_fisioterapeutas(service)
        fisio_disponivel = bool(fisioterapeutas)

        if fisio_disponivel:
            labels_fisio, options_fisio = _build_options(
                fisioterapeutas, lambda f: f"[{f.id}] {f.nome}"
            )
            escolha_fisio = st.selectbox(
                "Fisioterapeuta",
                labels_fisio,
                key="edit_escolha_fisioterapeuta",
            )
            fisioterapeuta_id = options_fisio[escolha_fisio].id
        else:
            st.info("Cadastre fisioterapeutas primeiro.")
            fisioterapeuta_id = None

        submitted = st.form_submit_button("Editar", disabled=not fisio_disponivel)

    if not fisio_disponivel or not submitted:
        return

    if not _validar_campos(nome, email, telefone_raw, data_entrada):
        return

    fone_digits = only_digits(telefone_raw or "")
    dia_kwargs = {attr: (dia_nome in dias_selecionados) for dia_nome, attr in DIAS}

    try:
        paciente_editado, updates = service.editar_paciente(
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

        st.success(f"Editado #{paciente_editado.id}")
        for campo, (antes, depois) in (updates or {}).items():
            st.success(f'[EDIT] {campo}: "{antes}" → "{depois}"')

        sleep(2)
        rerun_app()

    except Exception as exc:
        st.error(f"Erro ao editar paciente: {exc}")
        logger.error("Erro ao editar paciente: %s", exc, exc_info=True)
