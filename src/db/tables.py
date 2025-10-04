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

    aula_seg = Column(Boolean, nullable=False, default=False)
    aula_ter = Column(Boolean, nullable=False, default=False)
    aula_qua = Column(Boolean, nullable=False, default=False)
    aula_qui = Column(Boolean, nullable=False, default=False)
    aula_sex = Column(Boolean, nullable=False, default=False)
    aula_sab = Column(Boolean, nullable=False, default=False)
    aula_dom = Column(Boolean, nullable=False, default=False)


class UserSQL(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
