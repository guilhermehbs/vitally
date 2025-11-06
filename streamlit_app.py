from __future__ import annotations

import logging
import re

import streamlit as st

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

APP_TITLE = "🩺 Vitally"
PAGE_ICON = "🩺"
LAYOUT = "wide"
logger = logging.getLogger("vitally_app")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _wrap_named(title: str, fn, service: ClinicaService):
    def _page():
        fn(service)

    _page.__name__ = f"page__{_slug(title)}"
    return _page


def main() -> None:
    st.set_page_config(page_title="Vitally", page_icon=PAGE_ICON, layout=LAYOUT)

    if not ensure_auth():
        return
    user = st.session_state["auth_user"]
    header_userbar(user)
    st.title(APP_TITLE)

    try:
        service = ClinicaService()
    except Exception as exc:
        st.error(f"Falha ao inicializar serviços: {exc}")
        return

    CATALOG = {
        "Paciente": [
            ("Lista de pacientes", render_list_pacientes_tab),
            ("Editar pacientes", render_edit_pacientes_tab),
            ("Adicionar pacientes", render_add_pacientes_tab),
            ("Aulas dos pacientes", render_paciente_classes_tab),
        ],
        "Fisioterapeuta": [
            ("Lista de fisioterapeutas", render_list_fisioterapeutas_tab),
            ("Disponibilidades de fisioterapeutas", render_fisioterapeutas_disponibilidade_tab),
            ("Horários dos fisioterapeutas", render_fisioterapeutas_horarios_tab),
        ],
        "Pagamento": [
            ("Lista de pagamentos", render_pagamentos_tab),
            ("Proximos pagamentos", render_proximos_pagamentos_tab),
        ],
        "Matriz": [
            ("Matriz de Mobilidade & Estabilidade", render_matriz_me_tab),
        ],
    }

    pages = {
        group: [st.Page(_wrap_named(title, fn, service), title=title) for (title, fn) in items]
        for group, items in CATALOG.items()
    }

    st.navigation(pages, position="top").run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    main()
