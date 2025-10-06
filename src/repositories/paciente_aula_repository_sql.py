from sqlalchemy import delete, select

from src.db.db import SessionLocal
from src.db.tables import PacienteAulaSQL


class PacienteAulaRepositorySQL:
    def __init__(self):
        self._Session = SessionLocal

    def set_aulas(self, paciente_id: int, aulas: list[tuple[int, str]]):
        from datetime import time

        with self._Session() as s:
            s.execute(delete(PacienteAulaSQL).where(PacienteAulaSQL.paciente_id == paciente_id))
            for wd, hhmm in aulas:
                hh, mm = map(int, hhmm.split(":"))
                s.add(PacienteAulaSQL(paciente_id=paciente_id, weekday=wd, hora=time(hh, mm)))
            s.commit()

    def listar_por_paciente(self, paciente_id: int):
        with self._Session() as s:
            stmt = select(PacienteAulaSQL).where(PacienteAulaSQL.paciente_id == paciente_id)
            return s.execute(stmt).scalars().all()
