from __future__ import annotations

from datetime import date
from typing import Iterable, Dict, Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.services import ClinicaService

APP_TITLE = '🩺 Vitally'
PAGE_ICON = '🩺'
LAYOUT = 'wide'

TAB_LABEL_LIST = '👥 Pacientes'
TAB_LABEL_ADD = '➕ Cadastrar'
TAB_LABEL_PAY = '💳 Pagamento'
TAB_LABEL_DUE = '📬 Vencimentos proximos'

DATE_FMT_DISPLAY = '%d/%m/%Y'


def rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        raise RuntimeError("Versão do Streamlit não possui rerun disponível")


def format_date_br(d: date | None) -> str:
    return d.strftime(DATE_FMT_DISPLAY) if d else ''


def make_dataframe(rows: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows))
    return df if not df.empty else pd.DataFrame()


def render_list_tab(service: ClinicaService) -> None:
    st.subheader('Lista de pacientes')
    only_active = st.checkbox('Somente ativos', value=True, key='chk_only_active')

    try:
        pacientes = service.listar_pacientes(only_active)
    except Exception as exc:
        st.error(f'Erro ao listar pacientes: {exc}')
        return

    if not pacientes:
        st.info('Nenhum paciente.')
        return

    rows = (
        {
            'Id': p.id,
            'Nome': p.nome,
            'Telefone': p.telefone,
            'Email': p.email,
            'Entrada': format_date_br(p.data_entrada),
            'Último pagagamento': format_date_br(p.data_ultimo_pagamento),
            'Próxima cobrança': format_date_br(p.data_proxima_cobranca),
            'Ativo': p.ativo,
        }
        for p in pacientes
    )

    df = make_dataframe(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_add_tab(service: ClinicaService) -> None:
    st.subheader('Cadastrar paciente')

    with st.form('form_add_paciente', clear_on_submit=False):
        nome = st.text_input('Nome', key='add_nome').strip()
        email = st.text_input('E-mail', key='add_email').strip()
        telefone = st.text_input('Telefone', key='add_telefone').strip()
        data_entrada = st.date_input(
            'Data de entrada',
            value=date.today(),
            format='DD/MM/YYYY',
            key='add_data_entrada',
        )

        submitted = st.form_submit_button('Cadastrar')

    if not submitted:
        return

    if not nome:
        st.error('Informe o nome.')
        return

    try:
        paciente = service.cadastrar_paciente(
            nome=nome, email=email, telefone=telefone, data_entrada=data_entrada
        )
        prox = format_date_br(paciente.data_proxima_cobranca)
        st.success(f'Cadastrado #{paciente.id}. Próx. cobrança: {prox}')
        rerun_app()
    except Exception as exc:
        st.error(f'Erro ao cadastrar paciente: {exc}')


def render_pay_tab(service: ClinicaService) -> None:
    st.subheader('Registrar pagamento')

    try:
        ativos = service.listar_pacientes(only_active=True)
    except Exception as exc:
        st.error(f'Erro ao carregar pacientes: {exc}')
        return

    if not ativos:
        st.info('Cadastre pacientes primeiro.')
        return

    options = {f'[{p.id}] {p.nome}': p.id for p in ativos}
    escolha_label = st.selectbox('Paciente', list(options.keys()), key='pay_escolha')

    data_pagamento = st.date_input(
        'Data do pagamento', value=date.today(), format='DD/MM/YYYY', key='pay_data'
    )

    if st.button('Registrar', type='primary', key='btn_registrar_pag'):
        try:
            paciente = service.registrar_pagamento(options[escolha_label], data_pagamento)
            prox = format_date_br(paciente.data_proxima_cobranca)
            st.success(f'Pagamento registrado. Próx. cobrança: {prox}')
            rerun_app()
        except Exception as exc:
            st.error(f'Erro ao registrar pagamento: {exc}')


def render_due_tab(service: ClinicaService) -> None:
    st.subheader('Vencimentos proximos')

    try:
        vencendo = service.vencimentos_proximos()
    except Exception as exc:
        st.error(f'Erro ao carregar vencimentos: {exc}')
        return

    if not vencendo:
        st.info('Sem vencimentos proximos.')
        return

    rows = (
        {
            'Id': p.id,
            'Nome': p.nome,
            'Email': p.email,
            'Telefone': p.telefone,
            'Vencimento': format_date_br(p.data_proxima_cobranca),
        }
        for p in vencendo
    )

    df = make_dataframe(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    # st.caption(
    #     'Envio automático: pode ser feito por um script/cron externo chamando o serviço '
    #     '(ou integrar aqui depois).'
    # )

def main() -> None:
    st.set_page_config(page_title='Vitally', page_icon=PAGE_ICON, layout=LAYOUT)
    st.title(APP_TITLE)

    service = ClinicaService()

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


if __name__ == '__main__':
    main()
