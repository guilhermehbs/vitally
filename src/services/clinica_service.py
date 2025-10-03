from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from src.models.paciente_model import Paciente
from src.repositories.paciente_repository_sql import PacienteRepositorySQL


class ClinicaService:
    def __init__(self, repo: PacienteRepositorySQL | None = None):
        self._repo = repo or PacienteRepositorySQL()

    def cadastrar_paciente(
        self, nome: str, email: str, telefone: str, data_entrada: date
    ) -> Paciente:
        nome = (nome or "").strip()
        email = (email or "").strip()
        telefone = (telefone or "").strip()
        return self._repo.cadastrar(nome, email, telefone, data_entrada)

    def editar_paciente(
        self,
        paciente_id: int,
        nome: str,
        email: str,
        telefone: str,
        data_entrada: date,
        aula_seg: bool | None = None,
        aula_ter: bool | None = None,
        aula_qua: bool | None = None,
        aula_qui: bool | None = None,
        aula_sex: bool | None = None,
        aula_sab: bool | None = None,
        aula_dom: bool | None = None,
    ) -> tuple[Paciente, dict[str, tuple[object, object]]]:
        nome = (nome or "").strip()
        email = (email or "").strip()
        telefone = (telefone or "").strip()
        return self._repo.editar(
            paciente_id=paciente_id,
            nome=nome,
            email=email,
            telefone=telefone,
            data_entrada=data_entrada,
            aula_seg=aula_seg,
            aula_ter=aula_ter,
            aula_qua=aula_qua,
            aula_qui=aula_qui,
            aula_sex=aula_sex,
            aula_sab=aula_sab,
            aula_dom=aula_dom,
        )

    def listar_pacientes(self, only_active: bool = True) -> Sequence[Paciente]:
        return self._repo.listar(only_active)

    def registrar_pagamento(self, paciente_id: int | str, data_pag: date) -> Paciente:
        if isinstance(paciente_id, str):
            paciente_id = int(paciente_id.strip())
        return self._repo.registrar_pagamento(paciente_id, data_pag)

    def vencimentos_proximos(self) -> Sequence[Paciente]:
        return self._repo.vencimentos_proximos()
