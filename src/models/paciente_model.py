from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class Paciente:
    id: str
    nome: str
    telefone: str
    email: str
    data_entrada: date
    data_ultimo_pagamento: date | None
    data_proxima_cobranca: date
    ativo: bool = True
