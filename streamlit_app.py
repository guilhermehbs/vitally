from __future__ import annotations

import logging
from datetime import date, timedelta
from time import sleep

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.security.auth import get_user_by_email, verify_password
from src.services.clinica_service import ClinicaService
from src.utils.add_utils import is_valid_email, only_digits, validate_br_phone
from src.utils.classes_utils import build_classes_csv, build_classes_ics
from src.utils.dataframe_utils import make_dataframe
from src.utils.streamlit_utils import rerun_app
from src.utils.user_utils import get_fisioterapeutas, get_paciente_ativos

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
TAB_LABEL_FISIO = "👩‍⚕️ Fisioterapeutas"
TAB_LABEL_FISIO_DISP = "👩‍⚕️ Fisioterapeutas Disp"
TAB_LABEL_FISIO_GRADE = "👩‍⚕️ Fisioterapeutas Grade"

DATE_FMT_DISPLAY = "%d/%m/%Y"


def format_date_br(d: date | None) -> str:
    return d.strftime(DATE_FMT_DISPLAY) if d else ""


def render_pacientes_list_tab(service: ClinicaService) -> None:
    st.subheader("Lista de pacientes")
    only_active = st.checkbox("Somente ativos", value=True, key="chk_only_active")
    logger.info("Listando pacientes (somente_ativos=%s)", only_active)

    try:
        pacientes = get_paciente_ativos(service)
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
        sleep(2)
        rerun_app()
    except Exception as exc:
        st.error(f"Erro ao cadastrar paciente: {exc}")
        logger.error("Erro ao cadastrar paciente: %s", exc, exc_info=True)


DIAS = [
    ("Segunda", "aula_seg"),
    ("Terça", "aula_ter"),
    ("Quarta", "aula_qua"),
    ("Quinta", "aula_qui"),
    ("Sexta", "aula_sex"),
    ("Sábado", "aula_sab"),
    ("Domingo", "aula_dom"),
]


def render_edit_tab(service: ClinicaService) -> None:
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
        email = st.text_input("E-mail", key="edit_email", value=email).strip()
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
        horarios: list[tuple[int, str]] = []
        for dia_nome in dias_selecionados:
            t = st.time_input(f"Horário em {dia_nome}", key=f"time_{dia_nome}")
            horarios.append((weekday_map[dia_nome], f"{t.hour:02d}:{t.minute:02d}"))

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


def render_table_tab(service: ClinicaService) -> None:
    st.subheader("Mapa de Exercícios (Pilates)")

    aparelhos = ["Solo", "Chair", "Cadillac", "Reformer", "Barrel"]
    segmentos = ["Cervical", "MMSS", "Tronco", "Abdômen", "MMII"]

    base_rows = []
    for ap in aparelhos:
        row = {"Aparelho": ap}
        for seg in segmentos:
            row[seg] = "M / E"
        base_rows.append(row)
    df_base = pd.DataFrame(base_rows)
    st.markdown("**Matriz de referência (fixa):**")
    st.dataframe(df_base, use_container_width=True, hide_index=True)
    st.divider()

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


def render_classes_tab(service: ClinicaService) -> None:
    st.subheader("Aulas")
    logger.info("Aba de aulas carregada")

    ativos = get_paciente_ativos(service)
    if not ativos:
        st.info("Cadastre pacientes primeiro.")
        return

    options = {f"[{p.id}] {p.nome}": p for p in ativos}
    escolha_label = st.selectbox("Paciente", list(options.keys()), key="classes_escolha")
    paciente = options[escolha_label]

    cols = []
    vals = []

    for dia_nome, attr in [
        ("Seg", "aula_seg"),
        ("Ter", "aula_ter"),
        ("Qua", "aula_qua"),
        ("Qui", "aula_qui"),
        ("Sex", "aula_sex"),
        ("Sáb", "aula_sab"),
        ("Dom", "aula_dom"),
    ]:
        cols.append(dia_nome)
        vals.append("X" if getattr(paciente, attr, False) else "")

    df = pd.DataFrame([vals], columns=cols, index=[f"[{paciente.id}] {paciente.nome}"])
    st.dataframe(df, use_container_width=True)

    st.markdown("### Exportar plano de aulas")

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        csv_bytes = build_classes_csv(paciente)
        st.download_button(
            label="Baixar CSV (dias de aula)",
            data=csv_bytes,
            file_name=f"plano_aulas_{paciente.id}_{paciente.nome}.csv",
            mime="text/csv",
            key=f"dl_csv_classes_{paciente.id}",
        )

    with col_b:
        ics_bytes = build_classes_ics(
            paciente=paciente,
            start_on=date.today(),
            start_time_str="08:00",
            duration_minutes=60,
            tzid="America/Sao_Paulo",
        )
        st.download_button(
            label="Baixar .ics (calendário semanal)",
            data=ics_bytes,
            file_name=f"plano_aulas_{paciente.id}_{paciente.nome}.ics",
            mime="text/calendar",
            key=f"dl_ics_classes_{paciente.id}",
        )

    with col_c:
        st.caption(
            "• CSV: visão simples dos dias marcados (Sim/Não).  \n"
            "• ICS: evento semanal recorrente com BYDAY (usado "
            "para importar no calendário Google/Outlook)."
        )


def render_pay_tab(service: ClinicaService) -> None:
    st.subheader("Registrar pagamento")
    logger.info("Aba de pagamento carregada")

    ativos = get_paciente_ativos(service)
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


def ensure_auth() -> bool:
    if st.session_state.get("auth_user"):
        return True

    st.title("🩺 Vitally")
    st.subheader("Entrar")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("E-mail").strip()
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if not email or not password:
            st.error("Informe e-mail e senha.")
            return False

        user = get_user_by_email(email)
        if not user:
            st.error("Usuário não encontrado ou inativo.")
            return False

        if not verify_password(password, user.password_hash):
            st.error("Senha inválida.")
            return False

        st.session_state.auth_user = {"id": user.id, "name": user.name, "email": user.email}
        st.success(f"Bem-vindo(a), {user.name}!")
        st.rerun()

    return False


def logout_button() -> None:
    with st.sidebar:
        if st.button("Sair"):
            st.session_state.pop("auth_user", None)
            st.experimental_rerun()


def header_userbar(user: dict):
    st.markdown(
        """
                    <style>
                    .vitally-popover { width: 250px; }
                    .vitally-popover .stMarkdown { margin-bottom: .25rem; }
                    .vitally-popover hr { margin: .25rem 0; }
                    </style>
                """,
        unsafe_allow_html=True,
    )
    _, col_user = st.columns([0.85, 0.15], vertical_alignment="center")
    with col_user:
        try:
            with st.popover(f"👤 {user['name']}"):
                st.markdown("<div class='vitally-popover'>", unsafe_allow_html=True)
                st.caption(user["email"])
                st.divider()
                if st.button("Sair", key="logout_small"):
                    st.session_state.pop("auth_user", None)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.markdown(
                f"<div style='text-align:right;'>👤 <b>{user['name']}</b></div>",
                unsafe_allow_html=True,
            )
            if st.button("Sair", key="logout_top", use_container_width=True):
                st.session_state.pop("auth_user", None)
                st.rerun()


def render_fisio_tab(service: ClinicaService) -> None:
    st.subheader("Cadastro de Fisioterapeutas")
    with st.form("form_add_fisio"):
        nome = st.text_input("Nome").strip()
        email = st.text_input("E-mail (opcional)").strip()
        ok = st.form_submit_button("Cadastrar")
    if ok:
        if not nome:
            st.error("Informe o nome.")
        else:
            service.criar_fisioterapeuta(nome, email or None)
            st.success("Fisioterapeuta cadastrado.")
            rerun_app()

    st.divider()
    st.markdown("### Ativos")
    fisios = get_fisioterapeutas(service)
    st.dataframe(
        make_dataframe({"Id": f.id, "Nome": f.nome, "E-mail": f.email} for f in fisios),
        use_container_width=True,
        hide_index=True,
    )


def render_fisio_dispon_tab(service: ClinicaService) -> None:
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
    rows = []
    with st.form("form_dispon"):
        st.caption("Preencha as janelas (opcional deixar em branco)")
        for d in dias:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                on = st.checkbox(d, key=f"chk_{d}")
            with c2:
                h1 = st.time_input("Início", key=f"ini_{d}", disabled=not on)
            with c3:
                h2 = st.time_input("Fim", key=f"fim_{d}", disabled=not on)
            if on:
                rows.append(
                    (
                        weekday_map[d],
                        f"{h1.hour:02d}:{h1.minute:02d}",
                        f"{h2.hour:02d}:{h2.minute:02d}",
                    )
                )
        ok = st.form_submit_button("Salvar disponibilidades")

    if ok:
        service.definir_disponibilidades_fisio(fisio.id, rows)
        st.success("Disponibilidades salvas.")


def render_grade_fisio_tab(service: ClinicaService) -> None:
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
        slot_min = st.number_input("Tamanho do slot (min)", value=60, min_value=15, step=15)

    data_fim = semana_ini + timedelta(days=6)
    itens = service.grade_do_fisio(fisio.id, semana_ini, data_fim)

    try:
        todos = service.listar_pacientes(only_active=False)
        nome_by_id = {p.id: p.nome for p in todos}
    except Exception:
        nome_by_id = {}

    import pandas as pd

    dias = [semana_ini + timedelta(days=i) for i in range(7)]
    horas = []
    from datetime import datetime, time
    from datetime import timedelta as td

    dia_start = time(6, 0)
    dia_end = time(22, 0)
    cur = datetime.combine(semana_ini, dia_start)
    end = datetime.combine(semana_ini, dia_end)
    while cur.time() <= end.time():
        horas.append(cur.time().strftime("%H:%M"))
        cur += td(minutes=slot_min)

    grid = {h: {d.strftime("%a %d/%m"): "" for d in dias} for h in horas}

    for ag in itens:
        chave_col = ag.data.strftime("%a %d/%m")
        chave_linha = ag.hora_inicio.strftime("%H:%M")
        nome = ""
        if ag.paciente_id:
            nome = nome_by_id.get(ag.paciente_id, f"#{ag.paciente_id}")
        grid.setdefault(chave_linha, {})[chave_col] = nome or "Livre"

    df = pd.DataFrame.from_dict(grid, orient="index")[list(c for c in grid[horas[0]].keys())]
    st.dataframe(df, use_container_width=True)


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
        render_pacientes_list_tab(service)

    with tab_add:
        render_add_tab(service)

    with tab_edit:
        render_edit_tab(service)

    with tab_table:
        render_table_tab(service)

    with tab_classes:
        render_classes_tab(service)

    with tab_pay:
        render_pay_tab(service)

    with tab_due:
        render_due_tab(service)

    with tab_fisio:
        render_fisio_tab(service)

    with tab_fisio_disp:
        render_fisio_dispon_tab(service)

    with tab_fisio_grade:
        render_grade_fisio_tab(service)


if __name__ == "__main__":
    main()
