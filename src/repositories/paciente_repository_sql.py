from datetime import date, timedelta

from sqlalchemy import select

from src.db.tables import PacienteSQL
from src.models.paciente_model import Paciente

from ..db.db import SessionLocal


class PacienteRepositorySQL:
    def __init__(self):
        self._Session = SessionLocal

    def _to_model(self, row: PacienteSQL) -> Paciente:
        return Paciente(
            id=row.id,
            nome=row.nome,
            email=row.email,
            telefone=row.telefone,
            data_entrada=row.data_entrada,
            data_ultimo_pagamento=row.data_ultimo_pagamento,
            data_proxima_cobranca=row.data_proxima_cobranca,
            ativo=row.ativo,
        )

    def listar(self, only_active: bool) -> list[Paciente]:
        with self._Session() as s:
            stmt = select(PacienteSQL)
            if only_active:
                stmt = stmt.filter(PacienteSQL.ativo.is_(True))
            rows = s.execute(stmt).scalars().all()
            return [self._to_model(r) for r in rows]

    def cadastrar(self, nome: str, email: str, telefone: str, data_entrada: date) -> Paciente:
        with self._Session() as s:
            row = PacienteSQL(
                nome=nome,
                email=email or None,
                telefone=telefone or None,
                data_entrada=data_entrada,
                ativo=True,
                data_proxima_cobranca=(data_entrada + timedelta(days=30)) if data_entrada else None,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return self._to_model(row)

    def registrar_pagamento(self, paciente_id: int, data_pagamento: date) -> Paciente:
        with self._Session() as s:
            row = s.get(PacienteSQL, paciente_id)
            if not row:
                raise ValueError(f"Paciente {paciente_id} não encontrado")
            row.data_ultimo_pagamento = data_pagamento
            row.data_proxima_cobranca = (
                (data_pagamento + timedelta(days=30)) if data_pagamento else None
            )
            s.commit()
            s.refresh(row)
            return self._to_model(row)

    def vencimentos_proximos(self) -> list[Paciente]:
        from datetime import date as _date

        hoje = _date.today()
        limite = hoje + timedelta(days=7)
        with self._Session() as s:
            stmt = (
                select(PacienteSQL)
                .where(PacienteSQL.ativo.is_(True))
                .where(PacienteSQL.data_proxima_cobranca.is_not(None))
                .where(PacienteSQL.data_proxima_cobranca <= limite)
            )
            rows = s.execute(stmt).scalars().all()
            return [self._to_model(r) for r in rows]
