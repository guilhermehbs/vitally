from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class Paciente:
    id: int
    nome: str
    telefone: str
    email: str
    data_entrada: date
    data_ultimo_pagamento: date | None
    data_proxima_cobranca: date
    ativo: bool = True
    aula_seg: bool = False
    aula_ter: bool = False
    aula_qua: bool = False
    aula_qui: bool = False
    aula_sex: bool = False
    aula_sab: bool = False
    aula_dom: bool = False
