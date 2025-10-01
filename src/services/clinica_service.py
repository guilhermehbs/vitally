from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence, Protocol, Callable

from src.models import PacienteModel
from src.repositories import PacienteRepository


class PacienteRepositoryProtocol(Protocol):
    def add_paciente(self, nome: str, email: str, telefone: str, data_entrada: date) -> PacienteModel: ...
    def list_all(self, only_active: bool = True) -> Sequence[PacienteModel]: ...
    def registrar_pagamento(self, paciente_id: str, data_pag: date) -> PacienteModel: ...
    def list_due_on(self, dia: date) -> Sequence[PacienteModel]: ...


class ClinicaService:
    def __init__(self, repo: PacienteRepositoryProtocol | None = None, when_fn: Callable[[], date] | None = None) -> None:
        self._repo: PacienteRepositoryProtocol = repo or PacienteRepository()
        self._today: Callable[[], date] = when_fn or date.today

    def cadastrar_paciente(self, nome: str, email: str, telefone: str, data_entrada: date) -> PacienteModel:
        return self._repo.add_paciente(nome.strip(), email.strip(), telefone.strip(), data_entrada)

    def listar_pacientes(self, only_active: bool = True) -> Sequence[PacienteModel]:
        return self._repo.list_all(only_active)

    def registrar_pagamento(self, paciente_id: str, data_pag: date) -> PacienteModel:
        return self._repo.registrar_pagamento(paciente_id.strip(), data_pag)

    def vencimentos_proximos(self, dias: int = 7) -> Sequence[PacienteModel]:
        hoje = self._today()
        resultados: list[PacienteModel] = []
        for i in range(dias + 1):
            dia = hoje + timedelta(days=i)
            resultados.extend(self._repo.list_due_on(dia))
        return resultados
