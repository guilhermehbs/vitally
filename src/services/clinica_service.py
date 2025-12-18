from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_

from src.db.db import SessionLocal
from src.db.tables import AgendaSQL, FisioDisponSQL
from src.models.paciente_model import Paciente
from src.repositories.agenda_repository_sql import AgendaRepositorySQL
from src.repositories.fisioterapeuta_repository_sql import FisioterapeutaRepositorySQL
from src.repositories.paciente_aula_repository_sql import PacienteAulaRepositorySQL
from src.repositories.paciente_repository_sql import PacienteRepositorySQL


class ClinicaService:
    def __init__(
        self,
        repo: PacienteRepositorySQL | None = None,
        fisio_repo: FisioterapeutaRepositorySQL | None = None,
        aula_repo: PacienteAulaRepositorySQL | None = None,
        agenda_repo: AgendaRepositorySQL | None = None,
    ):
        self._repo = repo or PacienteRepositorySQL()
        self._fisio_repo = fisio_repo or FisioterapeutaRepositorySQL()
        self._aula_repo = aula_repo or PacienteAulaRepositorySQL()
        self._agenda_repo = agenda_repo or AgendaRepositorySQL()

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

    # --- Fisioterapeutas ---
    def criar_fisioterapeuta(self, nome: str, email: str | None):
        return self._fisio_repo.criar(nome, email)

    def listar_fisioterapeutas(self):
        return self._fisio_repo.listar_ativos()

    def definir_disponibilidades_fisio(self, fisio_id: int, slots: list[tuple[int, str, str]]):
        return self._fisio_repo.set_disponibilidades(fisio_id, slots)

    # --- Aulas ---
    def definir_aulas_paciente(
        self,
        paciente_id: int,
        aulas: list[tuple[int, str]],
        fisioterapeuta_id: int,
        duracao_min: int = 60,
        semanas: int = 4,
        data_inicio: date | None = None,
    ):
        self._aula_repo.set_aulas(paciente_id, aulas)

        self._materializar_agenda_aulas(
            paciente_id=paciente_id,
            fisio_id=fisioterapeuta_id,
            aulas=aulas,
            duracao_min=duracao_min,
            semanas=semanas,
            data_inicio=data_inicio or date.today(),
        )

    def aulas_do_paciente(self, paciente_id: int):
        return self._aula_repo.listar_por_paciente(paciente_id)

    # --- Agenda ---
    def grade_do_fisio(self, fisio_id: int, data_inicio, data_fim):
        return self._agenda_repo.listar_grade(fisio_id, data_inicio, data_fim)

    # ----------------- helpers privados -----------------

    def _materializar_agenda_aulas(
        self,
        paciente_id: int,
        fisio_id: int,
        aulas: list[tuple[int, str]],
        duracao_min: int,
        semanas: int,
        data_inicio: date,
    ) -> None:
        with SessionLocal() as s:
            disp_map: dict[int, list[tuple[time, time]]] = {}
            disp_rows = s.query(FisioDisponSQL).filter(FisioDisponSQL.fisio_id == fisio_id).all()
            for d in disp_rows:
                disp_map.setdefault(d.weekday, []).append((d.hora_inicio, d.hora_fim))

            data_fim = data_inicio + timedelta(days=7 * semanas - 1)

            for wd, hhmm in aulas:
                primeira_data = self._next_weekday_on_or_after(data_inicio, wd)
                hh, mm = map(int, hhmm.split(":"))
                h_ini = time(hh, mm)
                dt_delta = timedelta(minutes=duracao_min)
                cur = primeira_data
                while cur <= data_fim:
                    h_fim_dt = (datetime.combine(cur, h_ini) + dt_delta).time()

                    if self._hora_dentro_da_disponibilidade(disp_map.get(wd, []), h_ini, h_fim_dt):
                        if not self._existe_conflito(s, fisio_id, cur, h_ini, h_fim_dt):
                            s.add(
                                AgendaSQL(
                                    fisio_id=fisio_id,
                                    paciente_id=paciente_id,
                                    data=cur,
                                    hora_inicio=h_ini,
                                    hora_fim=h_fim_dt,
                                    status="agendado",
                                )
                            )
                    cur += timedelta(days=7)

            s.commit()

    @staticmethod
    def _next_weekday_on_or_after(start: date, target_wd: int) -> date:
        delta = (target_wd - start.weekday()) % 7
        return start + timedelta(days=delta)

    @staticmethod
    def _hora_dentro_da_disponibilidade(
        janelas: list[tuple[time, time]],
        h_ini: time,
        h_fim: time,
    ) -> bool:
        for j_ini, j_fim in janelas:
            if j_ini <= h_ini and j_fim >= h_fim:
                return True
        return False

    @staticmethod
    def _existe_conflito(
        s,
        fisio_id: int,
        data_: date,
        h_ini: time,
        h_fim: time,
    ) -> bool:
        q = (
            s.query(AgendaSQL)
            .filter(
                and_(
                    AgendaSQL.fisio_id == fisio_id,
                    AgendaSQL.data == data_,
                    AgendaSQL.status != "cancelado",
                    or_(
                        and_(AgendaSQL.hora_inicio <= h_ini, AgendaSQL.hora_fim > h_ini),
                        and_(AgendaSQL.hora_inicio < h_fim, AgendaSQL.hora_fim >= h_fim),
                        and_(AgendaSQL.hora_inicio >= h_ini, AgendaSQL.hora_fim <= h_fim),
                    ),
                )
            )
            .first()
        )
        return q is not None

    def deletar_paciente(self, paciente_id: int) -> None:
        self._repo.deletar(paciente_id)

    def inativar_paciente(self, paciente_id: int) -> None:
        self._repo.inativar(paciente_id)
