from datetime import date, timedelta

from src.repositories.paciente_repository_sql import PacienteRepositorySQL

def _mk_repo():
    return PacienteRepositorySQL()

def test_cadastrar_e_listar(db_session, monkeypatch):
    repo = _mk_repo()

    p1 = repo.cadastrar(nome="Alice", email="a@a.com", telefone="31999999999", data_entrada=date(2025, 1, 1))
    assert p1.id is not None
    assert p1.ativo is True

    p2 = repo.cadastrar(nome="Bob", email=None, telefone=None, data_entrada=date(2025, 1, 2))
    assert p2.id is not None

    from src.db import SessionLocal
    from src.models_sql import PacienteSQL

    with SessionLocal() as s:
        row = s.get(PacienteSQL, p2.id)
        row.ativo = False
        s.commit()

    ativos = repo.listar(only_active=True)
    assert len(ativos) == 1
    assert ativos[0].nome == "Alice"

    todos = repo.listar(only_active=False)
    assert {x.nome for x in todos} == {"Alice", "Bob"}

def test_registrar_pagamento_atualiza_datas(db_session):
    repo = _mk_repo()
    p = repo.cadastrar(nome="Carol", email=None, telefone=None, data_entrada=date(2025, 1, 10))
    assert p.data_proxima_cobranca is not None

    data_pag = date(2025, 2, 1)
    p2 = repo.registrar_pagamento(paciente_id=p.id, data_pagamento=data_pag)
    assert p2.data_ultimo_pagamento == data_pag
    assert p2.data_proxima_cobranca == data_pag + timedelta(days=30)

def test_vencimentos_proximos(db_session):
    repo = _mk_repo()

    hoje = date.today()
    dentro_da_janela = hoje + timedelta(days=5)
    fora_da_janela = hoje + timedelta(days=15)

    p_ok = repo.cadastrar(nome="Diego", email=None, telefone=None, data_entrada=hoje)

    from src.db import SessionLocal
    from src.models_sql import PacienteSQL

    with SessionLocal() as s:
        row = s.get(PacienteSQL, p_ok.id)
        row.data_proxima_cobranca = dentro_da_janela
        row.ativo = True
        s.commit()

    p_nok = repo.cadastrar(nome="Eva", email=None, telefone=None, data_entrada=hoje)
    with SessionLocal() as s:
        row = s.get(PacienteSQL, p_nok.id)
        row.data_proxima_cobranca = fora_da_janela
        row.ativo = True
        s.commit()

    p_inativo = repo.cadastrar(nome="Fred", email=None, telefone=None, data_entrada=hoje)
    with SessionLocal() as s:
        row = s.get(PacienteSQL, p_inativo.id)
        row.data_proxima_cobranca = dentro_da_janela
        row.ativo = False
        s.commit()

    venc = repo.vencimentos_proximos()
    nomes = {x.nome for x in venc}
    assert nomes == {"Diego"}
