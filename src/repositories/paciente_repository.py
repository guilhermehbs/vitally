from __future__ import annotations

import os, uuid, streamlit as st, pandas as pd

from datetime import date, timedelta
from typing import Optional, Callable, Iterable

from src.models import PacienteModel
from src.handlers import GoogleSheetsHandler


COLS: list[str] = [
    "id",
    "nome",
    "telefone",
    "email",
    "data_entrada",
    "data_ultimo_pagamento",
    "data_proxima_cobranca",
    "ativo",
]

A1_DEFAULT_RANGE = "A1:Z"


def _to_bool(x: object) -> bool:
    return str(x).strip().lower() in {"true", "1", "sim", "y"}


def _iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def _from_iso(s: Optional[str]) -> Optional[date]:
    s = (s or "").strip()
    return date.fromisoformat(s) if s else None


def _calc_prox(entrada: date, ultimo: Optional[date]) -> date:
    return (ultimo or entrada) + timedelta(days=30)


class PacienteRepository:
    def __init__(self, *, sheets: Optional[GoogleSheetsHandler] = None, worksheet: Optional[str] = None, today_fn: Optional[Callable[[], date]] = None) -> None:
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", st.secrets.get("GOOGLE_SPREADSHEET_ID"))
        self._worksheet = os.getenv("GOOGLE_SHEETS_WORKSHEET", st.secrets.get("GOOGLE_SHEETS_WORKSHEET", "Pacientes"))
        if not spreadsheet_id:
            raise RuntimeError(
                "Defina GOOGLE_SPREADSHEET_ID (ou GOOGLE_SHEETS_URL) no .env. "
                "Veja SETUP.md para instruções."
            )
        self._sheets = sheets or GoogleSheetsHandler(spreadsheet_id=spreadsheet_id)
        self._today: Callable[[], date] = today_fn or date.today

    def list_all(self, only_active: bool = True) -> list[PacienteModel]:
        df = self._load_df()
        if df.empty:
            return []

        if only_active:
            df = df[df["ativo"].eq(True)]

        return list(self._to_pacientes(df.itertuples(index=False)))

    def add_paciente(self, nome: str, email: str, telefone: str, data_entrada: date) -> PacienteModel:
        paciente_id = str(uuid.uuid4())
        proxima_cobranca = _calc_prox(data_entrada, None)

        row_dict = {
            "id": paciente_id,
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "data_entrada": _iso(data_entrada),
            "data_ultimo_pagamento": "",
            "data_proxima_cobranca": _iso(proxima_cobranca),
            "ativo": True,
        }
        df = pd.DataFrame([row_dict])
        df_ordered = df[COLS]
        self._sheets.add_data_to_sheet(df_ordered, self._worksheet)

        return PacienteModel(
            id=paciente_id,
            nome=nome,
            telefone=telefone,
            email=email,
            data_entrada=data_entrada,
            data_ultimo_pagamento=None,
            data_proxima_cobranca=proxima_cobranca,
            ativo=True,
        )

    def find_by_id(self, pid: str) -> Optional[PacienteModel]:
        df = self._load_df()
        if df.empty:
            return None

        match = df[df["id"] == pid]
        if match.empty:
            return None

        return self._row_to_paciente(match.iloc[0])

    def registrar_pagamento(self, pid: str, data_pag: date) -> PacienteModel:
        df = self._load_df()
        if df.empty or pid not in set(df["id"]):
            raise ValueError("Paciente não encontrado")

        idx = df.index[df["id"] == pid][0]
        if not _to_bool(df.at[idx, "ativo"]):
            raise ValueError("Paciente inativo")

        entrada = _from_iso(df.at[idx, "data_entrada"])
        assert isinstance(entrada, date), "data_entrada inválida na planilha"

        prox = _calc_prox(entrada, data_pag)

        df.at[idx, "data_ultimo_pagamento"] = _iso(data_pag)
        df.at[idx, "data_proxima_cobranca"] = _iso(prox)
        df.at[idx, "ativo"] = True

        row_values = [str(df.at[idx, c]) for c in COLS]

        line_1based = idx + 2
        self._sheets.update_row_by_index(self._worksheet, line_1based, row_values)

        return PacienteModel(
            id=pid,
            nome=str(df.at[idx, "nome"]),
            telefone=str(df.at[idx, "telefone"]),
            email=str(df.at[idx, "email"]),
            data_entrada=entrada,
            data_ultimo_pagamento=data_pag,
            data_proxima_cobranca=prox,
            ativo=True,
        )

    def list_due_on(self, when: date) -> list[PacienteModel]:
        df = self._load_df()
        if df.empty:
            return []

        iso = _iso(when)
        df = df[df["ativo"].eq(True) & df["data_proxima_cobranca"].eq(iso)]
        return list(self._to_pacientes(df.itertuples(index=False)))

    def _load_df(self) -> pd.DataFrame:
        df = self._sheets.load_sheet_as_df(self._worksheet)
        if df.empty:
            return pd.DataFrame(columns=COLS)

        for c in COLS:
            if c not in df.columns:
                df[c] = ""

        df = df[COLS].copy()
        df["ativo"] = df["ativo"].map(_to_bool)
        return df

    @staticmethod
    def _row_to_paciente(r: pd.Series) -> PacienteModel:
        return PacienteModel(
            id=str(r["id"]),
            nome=str(r["nome"]),
            telefone=str(r["telefone"]),
            email=str(r["email"]),
            data_entrada=_from_iso(str(r["data_entrada"])) or date.min,
            data_ultimo_pagamento=_from_iso(str(r["data_ultimo_pagamento"])) if r["data_ultimo_pagamento"] else None,
            data_proxima_cobranca=_from_iso(str(r["data_proxima_cobranca"])),
            ativo=bool(r["ativo"]),
        )

    def _to_pacientes(self, rows: Iterable[pd.Series | pd.NamedTuple]) -> Iterable[PacienteModel]:
        for r in rows:
            get = (lambda k: getattr(r, k)) if hasattr(r, "_asdict") else (lambda k: r[k])
            yield PacienteModel(
                id=str(get("id")),
                nome=str(get("nome")),
                telefone=str(get("telefone")),
                email=str(get("email")),
                data_entrada=_from_iso(str(get("data_entrada"))) or date.min,
                data_ultimo_pagamento=_from_iso(str(get("data_ultimo_pagamento"))) if get("data_ultimo_pagamento") else None,
                data_proxima_cobranca=_from_iso(str(get("data_proxima_cobranca"))),
                ativo=bool(get("ativo")),
            )
