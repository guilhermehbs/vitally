from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True, frozen=True)
class PacienteModel:
    """
    Entidade de domínio que representa um paciente na clínica.
    Imutável (frozen) para evitar mutações acidentais durante o ciclo de vida.
    """

    id: str
    nome: str
    telefone: str
    email: str
    data_entrada: date
    data_ultimo_pagamento: Optional[date]
    data_proxima_cobranca: date
    ativo: bool = True
