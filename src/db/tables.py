from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

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


class FisioterapeutaSQL(Base):
    __tablename__ = "fisioterapeutas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    ativo = Column(Boolean, nullable=False, default=True)

    disponibilidades = relationship(
        "FisioDisponSQL", back_populates="fisio", cascade="all, delete-orphan"
    )


class FisioDisponSQL(Base):
    __tablename__ = "fisio_disponibilidades"
    id = Column(Integer, primary_key=True)
    fisio_id = Column(
        Integer, ForeignKey("fisioterapeutas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weekday = Column(Integer, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)

    fisio = relationship("FisioterapeutaSQL", back_populates="disponibilidades")


class PacienteAulaSQL(Base):
    __tablename__ = "paciente_aulas"
    id = Column(Integer, primary_key=True)
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weekday = Column(Integer, nullable=False)
    hora = Column(Time, nullable=False)


class AgendaSQL(Base):
    __tablename__ = "agenda"
    id = Column(Integer, primary_key=True)
    fisio_id = Column(
        Integer, ForeignKey("fisioterapeutas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paciente_id = Column(
        Integer, ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    data = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)
    status = Column(String, nullable=False, default="agendado")
