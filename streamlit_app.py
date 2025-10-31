from __future__ import annotations

import logging

import streamlit as st
from dotenv import load_dotenv

from src.pages import (
    ensure_auth,
    header_userbar,
    render_add_pacientes_tab,
    render_edit_pacientes_tab,
    render_fisioterapeutas_disponibilidade_tab,
    render_fisioterapeutas_horarios_tab,
    render_list_fisioterapeutas_tab,
    render_list_pacientes_tab,
    render_matriz_me_tab,
    render_paciente_classes_tab,
    render_pagamentos_tab,
    render_proximos_pagamentos_tab,
)
from src.services.clinica_service import ClinicaService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vitally_app")

load_dotenv()
logger.info("Iniciando aplicação Vitally")

try:
    from src.db.db import Base, engine

    Base.metadata.create_all(bind=engine)
    logger.info("Verificação/criação de tabelas concluída")
except Exception as e:
    logger.error("Falha ao criar/verificar tabelas: %s", e, exc_info=True)

APP_TITLE = "🩺 Vitally"
PAGE_ICON = "🩺"
LAYOUT = "wide"

TAB_LABEL_LIST = "👥 Lista de Pacientes"
TAB_LABEL_ADD = "➕ Novo Paciente"
TAB_LABEL_EDIT = "✍️ Editar Paciente"
TAB_LABEL_TABLE = "📊 Matriz de Mobilidade & Estabilidade"
TAB_LABEL_CLASSES = "📅 Plano de Aulas"
TAB_LABEL_PAY = "💰 Pagamentos"
TAB_LABEL_DUE = "⏰ Próximos Vencimentos"
TAB_LABEL_FISIO = "👩‍⚕️ Lista de Fisioterapeutas"
TAB_LABEL_FISIO_DISP = "👩‍⚕️📆 Disponibilidade de Fisioterapeutas"
TAB_LABEL_FISIO_GRADE = "👩‍⚕️⌚ Horários de Fisioterapeutas"


def main() -> None:
    st.set_page_config(page_title="Vitally", page_icon=PAGE_ICON, layout=LAYOUT)

    if not ensure_auth():
        return

    user = st.session_state["auth_user"]
    header_userbar(user)
    logging.info(f"Usuário logado: ID: {user['id']}, Name: {user['name']}, Email: {user['email']}")

    st.title(APP_TITLE)
    logger.info("Página carregada")

    try:
        service = ClinicaService()
        logger.info("ClinicaService inicializado")
    except Exception as exc:
        logger.critical("Falha ao inicializar ClinicaService: %s", exc, exc_info=True)
        st.error(f"Falha ao inicializar serviços: {exc}")
        return

    (
        tab_list,
        tab_add,
        tab_edit,
        tab_table,
        tab_classes,
        tab_pay,
        tab_due,
        tab_fisio,
        tab_fisio_disp,
        tab_fisio_grade,
    ) = st.tabs(
        [
            TAB_LABEL_LIST,
            TAB_LABEL_ADD,
            TAB_LABEL_EDIT,
            TAB_LABEL_TABLE,
            TAB_LABEL_CLASSES,
            TAB_LABEL_PAY,
            TAB_LABEL_DUE,
            TAB_LABEL_FISIO,
            TAB_LABEL_FISIO_DISP,
            TAB_LABEL_FISIO_GRADE,
        ]
    )

    with tab_list:
        render_list_pacientes_tab(service)

    with tab_add:
        render_add_pacientes_tab(service)

    with tab_edit:
        render_edit_pacientes_tab(service)

    with tab_table:
        render_matriz_me_tab(service)

    with tab_classes:
        render_paciente_classes_tab(service)

    with tab_pay:
        render_pagamentos_tab(service)

    with tab_due:
        render_proximos_pagamentos_tab(service)

    with tab_fisio:
        render_list_fisioterapeutas_tab(service)

    with tab_fisio_disp:
        render_fisioterapeutas_disponibilidade_tab(service)

    with tab_fisio_grade:
        render_fisioterapeutas_horarios_tab(service)


if __name__ == "__main__":
    main()
