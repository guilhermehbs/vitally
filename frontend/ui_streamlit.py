import pandas as pd
import streamlit as st
from datetime import date

from backend.services import ClinicaService

st.set_page_config(page_title="Clínica – Sheets MVP", page_icon="🩺", layout="wide")
st.title("🩺 Clínica (MVP) — Front (Streamlit) + Back (Serviço)")

svc = ClinicaService()

def to_br(d): return d.strftime("%d/%m/%Y") if d else ""

tab_list, tab_add, tab_pay, tab_due = st.tabs(["👥 Pacientes", "➕ Cadastrar", "💳 Pagamento", "📬 Hoje"])

with tab_list:
    only_active = st.checkbox("Somente ativos", value=True)
    pacs = svc.listar_pacientes(only_active)
    if pacs:
        df = pd.DataFrame([{
            "id": p.id, "nome": p.nome, "telefone": p.telefone, "email": p.email,
            "entrada": to_br(p.data_entrada),
            "último_pag": to_br(p.data_ultimo_pagamento),
            "próx_cobrança": to_br(p.data_proxima_cobranca),
            "ativo": p.ativo
        } for p in pacs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum paciente.")

with tab_add:
    st.subheader("Cadastrar paciente")
    with st.form("form_add"):
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        data_entrada = st.date_input("Data de entrada", value=date.today(), format="DD/MM/YYYY")
        ok = st.form_submit_button("Cadastrar")
        if ok:
            if not nome.strip():
                st.error("Informe o nome.")
            else:
                p = svc.cadastrar_paciente(nome.strip(), email.strip(), telefone.strip(), data_entrada)
                st.success(f"Cadastrado #{p.id}. Próx cobrança: {to_br(p.data_proxima_cobranca)}")
                st.experimental_rerun()

with tab_pay:
    st.subheader("Registrar pagamento")
    ativos = svc.listar_pacientes(True)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
    else:
        options = {f"[{p.id}] {p.nome}": p.id for p in ativos}
        escolha = st.selectbox("Paciente", list(options.keys()))
        data_pag = st.date_input("Data do pagamento", value=date.today(), format="DD/MM/YYYY")
        if st.button("Registrar"):
            try:
                p = svc.registrar_pagamento(options[escolha], data_pag)
                st.success(f"Ok! Próx cobrança: {to_br(p.data_proxima_cobranca)}")
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))

with tab_due:
    st.subheader("Vencimentos de hoje")
    due = svc.vencendo_hoje()
    if not due:
        st.info("Sem vencimentos hoje.")
    else:
        df = pd.DataFrame([{
            "id": p.id, "nome": p.nome, "email": p.email, "telefone": p.telefone,
            "vence_hoje": to_br(p.data_proxima_cobranca)
        } for p in due])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Envio automático: faça por um script/cron externo chamando o serviço (ou integre aqui depois).")
