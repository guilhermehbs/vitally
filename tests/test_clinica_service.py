from datetime import date, timedelta

from src.services import ClinicaService

def test_service_cadastrar_listar_fluxo_basico():
    svc = ClinicaService()
    p = svc.cadastrar_paciente(nome="Gabi", email="g@g.com", telefone="31988887777", data_entrada=date(2025, 1, 3))
    assert p.id is not None

    ativos = svc.listar_pacientes(only_active=True)
    assert any(x.id == p.id for x in ativos)

def test_service_registrar_pagamento():
    svc = ClinicaService()
    p = svc.cadastrar_paciente(nome="Heitor", email=None, telefone=None, data_entrada=date(2025, 1, 5))
    quando = date(2025, 2, 10)
    p2 = svc.registrar_pagamento(p.id, quando)
    assert p2.data_ultimo_pagamento == quando
    assert p2.data_proxima_cobranca == quando + timedelta(days=30)

def test_service_vencimentos_proximos():
    svc = ClinicaService()
    hoje = date.today()

    p = svc.cadastrar_paciente(nome="Iris", email=None, telefone=None, data_entrada=hoje)
    from src.db import SessionLocal
    from src.models_sql import PacienteSQL

    with SessionLocal() as s:
        row = s.get(PacienteSQL, p.id)
        row.data_proxima_cobranca = hoje + timedelta(days=3)
        s.commit()

    proximos = svc.vencimentos_proximos()
    assert any(x.id == p.id for x in proximos)
