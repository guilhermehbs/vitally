from sqlalchemy import Boolean, Column, Date, Integer, String

from .db import Base


class PacienteSQL(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    data_entrada = Column(Date, nullable=True)
    data_ultimo_pagamento = Column(Date, nullable=True)
    data_proxima_cobranca = Column(Date, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
