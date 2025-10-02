from sqlalchemy import inspect

from src.db.db import engine
from src.db.tables import PacienteSQL


def test_table_exists():
    insp = inspect(engine)
    tables = insp.get_table_names()
    assert "pacientes" in tables


def test_columns_schema():
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("pacientes")}
    assert {
        "id",
        "nome",
        "email",
        "telefone",
        "data_entrada",
        "data_ultimo_pagamento",
        "data_proxima_cobranca",
        "ativo",
    }.issubset(cols)


def test_pk_index():
    assert PacienteSQL.__table__.primary_key.columns.keys() == ["id"]
