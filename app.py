from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from datetime import date
from typing import Any

import pandas as pd
from dotenv import load_dotenv

import app as st
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

TAB_LABEL_LIST = "👥 Pacientes"
TAB_LABEL_ADD = "➕ Cadastrar"
TAB_LABEL_PAY = "💳 Pagamento"
TAB_LABEL_DUE = "📬 Vencimentos proximos"

DATE_FMT_DISPLAY = "%d/%m/%Y"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    if not email:
        logger.debug("is_valid_email: vazio -> True")
        return True
    ok = bool(EMAIL_RE.fullmatch(email))
    logger.debug("is_valid_email(%s) -> %s", email, ok)
    return ok


def only_digits(s: str) -> str:
    digits = re.sub(r"\D", "", s or "")
    logger.debug("only_digits(%s) -> %s", s, digits)
    return digits


def validate_br_phone(digits: str) -> tuple[bool, str | None]:
    d = only_digits(digits)
    if len(d) not in (10, 11):
        return False, "Telefone deve ter 10 (fixo) ou 11 (celular) dígitos."
    if d[0] == "0" or d[1] == "0":
        return False, "DDD inválido."
    if len(d) == 11 and d[2] != "9":
        return False, "Para celular (11 dígitos), o número deve começar com 9."
    return True, None


def rerun_app() -> None:
    logger.debug("Solicitando rerun do Streamlit")
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        logger.critical("Streamlit sem método de rerun disponível")
        raise RuntimeError("Versão do Streamlit não possui rerun disponível")


def format_date_br(d: date | None) -> str:
    return d.strftime(DATE_FMT_DISPLAY) if d else ""


def make_dataframe(rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows))
    return df if not df.empty else pd.DataFrame()


def render_list_tab(service: ClinicaService) -> None:
    st.subheader("Lista de pacientes")
    only_active = st.checkbox("Somente ativos", value=True, key="chk_only_active")
    logger.info("Listando pacientes (somente_ativos=%s)", only_active)

    try:
        pacientes = service.listar_pacientes(only_active)
        logger.info("Total retornado: %d", len(pacientes))
    except Exception as exc:
        st.error(f"Erro ao listar pacientes: {exc}")
        logger.error("Erro ao listar pacientes: %s", exc, exc_info=True)
        return

    if not pacientes:
        st.info("Nenhum paciente.")
        return

    rows = (
        {
            "Id": p.id,
            "Nome": p.nome,
            "Telefone": p.telefone,
            "Email": p.email,
            "Entrada": format_date_br(p.data_entrada),
            "Último pagamento": format_date_br(p.data_ultimo_pagamento),
            "Próxima cobrança": format_date_br(p.data_proxima_cobranca),
            "Ativo": p.ativo,
        }
        for p in pacientes
    )

    df = make_dataframe(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_add_tab(service: ClinicaService) -> None:
    st.subheader("Cadastrar paciente")
    logger.info("Aba de cadastro carregada")

    if "add_tel_mask" not in st.session_state:
        st.session_state.add_tel_mask = ""
    if "add_tel_digits" not in st.session_state:
        st.session_state.add_tel_digits = ""

    with st.form("form_add_paciente", clear_on_submit=False):
        nome = st.text_input("Nome", key="add_nome").strip()
        email = st.text_input("E-mail", key="add_email").strip()
        telefone_raw = st.text_input("Telefone", key="add_telefone", placeholder="31999999999")
        data_entrada = st.date_input(
            "Data de entrada",
            value=date.today(),
            format="DD/MM/YYYY",
            key="add_data_entrada",
        )
        submitted = st.form_submit_button("Cadastrar")

    if not submitted:
        return

    if not nome:
        st.error("Informe o nome.")
        return

    if email and not is_valid_email(email):
        st.error("E-mail inválido.")
        return

    fone_digits = only_digits(telefone_raw)
    ok, msg = validate_br_phone(fone_digits)
    if not ok:
        st.error(msg or "Telefone inválido. Digite DDD + número (ex.: 3199XXXXXXX ou 3130XXXXXX).")
        return

    try:
        paciente = service.cadastrar_paciente(
            nome=nome,
            email=email,
            telefone=fone_digits,
            data_entrada=data_entrada,
        )
        prox = format_date_br(paciente.data_proxima_cobranca)
        st.success(f"Cadastrado #{paciente.id}. Próx. cobrança: {prox}")
        rerun_app()
    except Exception as exc:
        st.error(f"Erro ao cadastrar paciente: {exc}")
        logger.error("Erro ao cadastrar paciente: %s", exc, exc_info=True)


def render_pay_tab(service: ClinicaService) -> None:
    st.subheader("Registrar pagamento")
    logger.info("Aba de pagamento carregada")

    try:
        ativos = service.listar_pacientes(only_active=True)
        logger.info("Total de pacientes ativos para pagamento: %d", len(ativos))
    except Exception as exc:
        st.error(f"Erro ao carregar pacientes: {exc}")
        logger.error("Erro ao carregar pacientes (pagamento): %s", exc, exc_info=True)
        return

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


def render_due_tab(service: ClinicaService) -> None:
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


def main() -> None:
    st.set_page_config(page_title="Vitally", page_icon=PAGE_ICON, layout=LAYOUT)
    st.title(APP_TITLE)
    logger.info("Página carregada")

    try:
        service = ClinicaService()
        logger.info("ClinicaService inicializado")
    except Exception as exc:
        logger.critical("Falha ao inicializar ClinicaService: %s", exc, exc_info=True)
        st.error(f"Falha ao inicializar serviços: {exc}")
        return

    tab_list, tab_add, tab_pay, tab_due = st.tabs(
        [TAB_LABEL_LIST, TAB_LABEL_ADD, TAB_LABEL_PAY, TAB_LABEL_DUE]
    )

    with tab_list:
        render_list_tab(service)

    with tab_add:
        render_add_tab(service)

    with tab_pay:
        render_pay_tab(service)

    with tab_due:
        render_due_tab(service)


if __name__ == "__main__":
    main()
