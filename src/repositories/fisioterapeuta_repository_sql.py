from sqlalchemy import delete, select

from src.db.db import SessionLocal
from src.db.tables import FisioDisponSQL, FisioterapeutaSQL


class FisioterapeutaRepositorySQL:
    def __init__(self):
        self._Session = SessionLocal

    def criar(self, nome: str, email: str | None) -> FisioterapeutaSQL:
        with self._Session() as s:
            row = FisioterapeutaSQL(
                nome=nome.strip(), email=(email or "").strip() or None, ativo=True
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return row

    def listar_ativos(self) -> list[FisioterapeutaSQL]:
        with self._Session() as s:
            stmt = select(FisioterapeutaSQL).where(FisioterapeutaSQL.ativo.is_(True))
            return s.execute(stmt).scalars().all()

    def set_disponibilidades(self, fisio_id: int, slots: list[tuple[int, str, str]]):
        from datetime import time

        with self._Session() as s:
            s.execute(delete(FisioDisponSQL).where(FisioDisponSQL.fisio_id == fisio_id))
            for wd, h1, h2 in slots:
                hh1, mm1 = map(int, h1.split(":"))
                hh2, mm2 = map(int, h2.split(":"))
                s.add(
                    FisioDisponSQL(
                        fisio_id=fisio_id,
                        weekday=wd,
                        hora_inicio=time(hh1, mm1),
                        hora_fim=time(hh2, mm2),
                    )
                )
            s.commit()
