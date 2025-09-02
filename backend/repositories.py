from datetime import date, timedelta
from typing import List, Optional
import uuid, os
import pandas as pd

from .repo_interface import PacienteRepository 
from .models import Paciente
from .handlers.sheets_handler import GoogleSheetsHandler

COLS = ["id","nome","telefone","email","data_entrada","data_ultimo_pagamento","data_proxima_cobranca","ativo"]

def _to_bool(x) -> bool:
    return str(x).lower() in ("true","1","sim","y")

def _iso(d: date | None) -> str:
    return d.isoformat() if d else ""

def _from_iso(s: str | None):
    return date.fromisoformat(s) if s else None

def _calc_prox(entrada: date, ultimo: date | None) -> date:
    return (ultimo or entrada) + timedelta(days=30)

class ApiSheetsPacienteRepository(PacienteRepository):
    def __init__(self) -> None:
        ss_id_or_url = os.getenv("GOOGLE_SPREADSHEET_ID") or os.getenv("GOOGLE_SHEETS_URL") or ""
        if not ss_id_or_url:
            raise RuntimeError("Defina GOOGLE_SPREADSHEET_ID (ou GOOGLE_SHEETS_URL) no arquivo .env. Veja SETUP.md para instruções.")
        self.sheet_title = os.getenv("GOOGLE_SHEETS_WORKSHEET", "Pacientes")
        self.handler = GoogleSheetsHandler(
            spreadsheet_id_or_url=ss_id_or_url,
            credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        )

    def _load_df(self) -> pd.DataFrame:
        df = self.handler.load_sheet_as_df(self.sheet_title)
        if df.empty:
            return pd.DataFrame(columns=COLS)
        for c in COLS:
            if c not in df.columns:
                df[c] = ""
        df = df[COLS].copy()
        df["ativo"] = df["ativo"].map(_to_bool)
        return df

    def list_all(self, only_active: bool = True) -> List[Paciente]:
        df = self._load_df()
        if df.empty:
            return []
        if only_active:
            df = df[df["ativo"] == True]
        pacs: List[Paciente] = []
        for _, r in df.iterrows():
            pacs.append(Paciente(
                id=str(r["id"]),
                nome=str(r["nome"]),
                telefone=str(r["telefone"]),
                email=str(r["email"]),
                data_entrada=_from_iso(str(r["data_entrada"])),
                data_ultimo_pagamento=_from_iso(str(r["data_ultimo_pagamento"])) if r["data_ultimo_pagamento"] else None,
                data_proxima_cobranca=_from_iso(str(r["data_proxima_cobranca"])),
                ativo=bool(r["ativo"]),
            ))
        return pacs

    def add(self, nome: str, email: str, telefone: str, data_entrada: date) -> Paciente:
        pid = str(uuid.uuid4())
        prox = _calc_prox(data_entrada, None)
        row = {
            "id": pid, "nome": nome, "telefone": telefone, "email": email,
            "data_entrada": _iso(data_entrada),
            "data_ultimo_pagamento": "",
            "data_proxima_cobranca": _iso(prox),
            "ativo": True
        }
        ordered = [row[c] for c in COLS]
        last = self.handler.get_last_filled_row(self.sheet_title, "A1:Z")
        start_cell = f"A{(last or 1) + 1}"
        self.handler.append_values(self.sheet_title, start_cell, [ordered])
        return Paciente(
            id=pid, nome=nome, telefone=telefone, email=email,
            data_entrada=data_entrada, data_ultimo_pagamento=None,
            data_proxima_cobranca=prox, ativo=True
        )

    def find_by_id(self, pid: str) -> Optional[Paciente]:
        df = self._load_df()
        if df.empty:
            return None
        m = df[df["id"] == pid]
        if m.empty:
            return None
        r = m.iloc[0]
        return Paciente(
            id=str(r["id"]),
            nome=str(r["nome"]),
            telefone=str(r["telefone"]),
            email=str(r["email"]),
            data_entrada=_from_iso(str(r["data_entrada"])),
            data_ultimo_pagamento=_from_iso(str(r["data_ultimo_pagamento"])) if r["data_ultimo_pagamento"] else None,
            data_proxima_cobranca=_from_iso(str(r["data_proxima_cobranca"])),
            ativo=bool(r["ativo"]),
        )

    def registrar_pagamento(self, pid: str, data_pag: date) -> Paciente:
        df = self._load_df()
        if df.empty or pid not in set(df["id"]):
            raise ValueError("Paciente não encontrado")
        idx = df.index[df["id"] == pid][0]
        if not _to_bool(df.at[idx, "ativo"]):
            raise ValueError("Paciente inativo")

        entrada = _from_iso(df.at[idx, "data_entrada"])
        prox = _calc_prox(entrada, data_pag)

        df.at[idx, "data_ultimo_pagamento"] = _iso(data_pag)
        df.at[idx, "data_proxima_cobranca"] = _iso(prox)
        df.at[idx, "ativo"] = True

        row_values = [str(df.at[idx, c]) for c in COLS]
        line_1based = idx + 2
        self.handler.update_row_by_index(self.sheet_title, line_1based, row_values)

        return Paciente(
            id=pid,
            nome=str(df.at[idx, "nome"]),
            telefone=str(df.at[idx, "telefone"]),
            email=str(df.at[idx, "email"]),
            data_entrada=entrada,
            data_ultimo_pagamento=data_pag,
            data_proxima_cobranca=prox,
            ativo=True,
        )

    def list_due_on(self, when: date) -> List[Paciente]:
        iso = _iso(when)
        df = self._load_df()
        if df.empty:
            return []
        df = df[(df["ativo"] == True) & (df["data_proxima_cobranca"] == iso)]
        return [Paciente(
            id=str(r["id"]),
            nome=str(r["nome"]),
            telefone=str(r["telefone"]),
            email=str(r["email"]),
            data_entrada=_from_iso(str(r["data_entrada"])),
            data_ultimo_pagamento=_from_iso(str(r["data_ultimo_pagamento"])) if r["data_ultimo_pagamento"] else None,
            data_proxima_cobranca=_from_iso(str(r["data_proxima_cobranca"])),
            ativo=True
        ) for _, r in df.iterrows()]
