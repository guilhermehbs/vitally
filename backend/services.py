from datetime import date
from typing import List

from backend.models import Paciente
from backend.repositories import PacienteRepository, ApiSheetsPacienteRepository

class ClinicaService:
    def __init__(self, repo: PacienteRepository | None = None):
        self.repo = repo or ApiSheetsPacienteRepository()

    # casos de uso
    def cadastrar_paciente(self, nome: str, email: str, telefone: str, data_entrada: date) -> Paciente:
        return self.repo.add(nome, email, telefone, data_entrada)

    def listar_pacientes(self, only_active: bool = True) -> List[Paciente]:
        return self.repo.list_all(only_active)

    def registrar_pagamento(self, paciente_id: str, data_pag: date) -> Paciente:
        return self.repo.registrar_pagamento(paciente_id, data_pag)

    def vencendo_hoje(self) -> List[Paciente]:
        return self.repo.list_due_on(date.today())
