from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
            aula_seg=row.aula_seg or False,
            aula_ter=row.aula_ter or False,
            aula_qua=row.aula_qua or False,
            aula_qui=row.aula_qui or False,
            aula_sex=row.aula_sex or False,
            aula_sab=row.aula_sab or False,
            aula_dom=row.aula_dom or False,
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

    def editar(
        self,
        paciente_id: int,
        *,
        nome: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
        data_entrada: date | None = None,
        aula_seg: bool | None = None,
        aula_ter: bool | None = None,
        aula_qua: bool | None = None,
        aula_qui: bool | None = None,
        aula_sex: bool | None = None,
        aula_sab: bool | None = None,
        aula_dom: bool | None = None,
    ) -> tuple[Paciente, dict[str, tuple[object, object]]]:
        def _norm_str(v: str | None) -> str | None:
            if v is None:
                return None
            v2 = v.strip()
            return v2 if v2 else None

        with self._Session() as s:
            row = s.get(PacienteSQL, paciente_id)
            if row is None:
                raise ValueError(f"Paciente id={paciente_id} não encontrado")

            updates: dict[str, tuple[object, object]] = {}

            if nome is not None and nome != row.nome:
                updates["nome"] = (row.nome, nome)

            if email is not None:
                e = _norm_str(email)
                if e != row.email:
                    updates["email"] = (row.email, e)

            if telefone is not None:
                t = _norm_str(telefone)
                if t != row.telefone:
                    updates["telefone"] = (row.telefone, t)

            if data_entrada is not None and data_entrada != row.data_entrada:
                updates["data_entrada"] = (row.data_entrada, data_entrada)
                updates["data_proxima_cobranca"] = (
                    row.data_proxima_cobranca,
                    data_entrada + timedelta(days=30),
                )

            for attr, new_val in {
                "aula_seg": aula_seg,
                "aula_ter": aula_ter,
                "aula_qua": aula_qua,
                "aula_qui": aula_qui,
                "aula_sex": aula_sex,
                "aula_sab": aula_sab,
                "aula_dom": aula_dom,
            }.items():
                if new_val is not None and getattr(row, attr) != new_val:
                    updates[attr] = (getattr(row, attr), new_val)

            if not updates:
                return self._to_model(row), {}

            for k, v in updates.items():
                setattr(row, k, v[1])

            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                raise

            s.refresh(row)
            return self._to_model(row), updates

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

    def deletar(self, paciente_id: int) -> None:
        with self._Session() as s:
            paciente = s.query(PacienteSQL).filter(PacienteSQL.id == paciente_id).first()

            if not paciente:
                raise ValueError("Paciente não encontrado")

            s.delete(paciente)
            s.commit()

    def inativar(self, paciente_id: int) -> None:
        with self._Session() as s:
            paciente = s.query(PacienteSQL).filter(PacienteSQL.id == paciente_id).first()

            if not paciente:
                raise ValueError("Paciente não encontrado")

            paciente.ativo = False
            s.commit()
