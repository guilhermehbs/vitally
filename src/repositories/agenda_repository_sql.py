from sqlalchemy import select

from src.db.db import SessionLocal
from src.db.tables import AgendaSQL


class AgendaRepositorySQL:
    def __init__(self):
        self._Session = SessionLocal

    def listar_grade(self, fisio_id: int, data_inicio, data_fim):
        with self._Session() as s:
            stmt = (
                select(AgendaSQL)
                .where(AgendaSQL.fisio_id == fisio_id)
                .where(AgendaSQL.data >= data_inicio)
                .where(AgendaSQL.data <= data_fim)
                .order_by(AgendaSQL.data.asc(), AgendaSQL.hora_inicio.asc())
            )
            return s.execute(stmt).scalars().all()
