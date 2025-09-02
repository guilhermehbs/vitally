from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Paciente:
    id: str
    nome: str
    telefone: str
    email: str
    data_entrada: date
    data_ultimo_pagamento: Optional[date]
    data_proxima_cobranca: date
    ativo: bool = True
