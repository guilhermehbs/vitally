from __future__ import annotations
import os, csv, socket, logging
from typing import List, Dict, Optional, Literal, Any

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

def col_letter(n: int) -> str:
    # 1 -> A, 8 -> H etc.
    res = ''
    while n:
        n, r = divmod(n - 1, 26)
        res = chr(65 + r) + res
    return res

def parse_spreadsheet_id(url_or_id: str) -> str:
    if "/spreadsheets/d/" in url_or_id:
        return url_or_id.split("/spreadsheets/d/")[1].split("/")[0].split("?")[0]
    return url_or_id

def catch_and_log_errors(fn):
    def _wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HttpError as err:
            logging.error(f"Erro Google API em {fn.__name__}: {err}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado em {fn.__name__}: {e}")
            raise
    return _wrap

class GoogleSheetsHandler:

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def __init__(
        self,
        spreadsheet_id_or_url: str,
        credentials_file: Optional[str] = None,
        timeout: int = 300,
    ) -> None:
        socket.setdefaulttimeout(timeout)
        self.spreadsheet_id = parse_spreadsheet_id(spreadsheet_id_or_url)
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self._sheet_id_cache: Dict[str, int] = {}
        self.sheet = self._build_service()

    @catch_and_log_errors
    def _build_service(self):
        creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.SCOPES)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return service.spreadsheets()

    def _range(self, sheet: str, cell_range: str) -> str:
        return f"{sheet}!{cell_range}"

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> List[List[str]]:
        return [list(map(str, row))[1:] for row in df.itertuples()]

    @staticmethod
    def _read_csv_file(filepath: str) -> List[List[str]]:
        with open(filepath, newline="") as f:
            return list(csv.reader(f))[1:]

    @catch_and_log_errors
    def get_values(self, sheet: str, cell_range: str) -> List[List[str]]:
        resp = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
        ).execute()
        return resp.get("values", [])

    @catch_and_log_errors
    def append_values(self, sheet: str, cell_range: str, values: List[List[str]]) -> None:
        self.sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        ).execute()

    @catch_and_log_errors
    def update_values(self, sheet: str, cell_range: str, values: List[List[str]]) -> None:
        self.sheet.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
            valueInputOption="RAW",
            body={"values": values},
        ).execute()

    @catch_and_log_errors
    def clear_values(self, sheet: str, cell_range: str) -> None:
        self.sheet.values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
        ).execute()

    @catch_and_log_errors
    def get_last_filled_row(self, sheet: str, scan_range: str = "A1:Z") -> int:
        vals = self.get_values(sheet, scan_range)
        return max((i + 1 for i, row in enumerate(vals) if any(str(c).strip() for c in row)), default=0)

    @catch_and_log_errors
    def add_data_to_sheet(self, df: pd.DataFrame, sheet: str) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Df deve ser um DataFrame")
        last = self.get_last_filled_row(sheet, "A1:Z")
        start = f"A{last + 1}"
        data = self._normalize_df(df)
        try:
            self.append_values(sheet, start, data)
        except HttpError as e:
            if "exceeds grid limits" in str(e):
                logging.warning("Limite de linhas excedido; adicionando mais linhas e tentando novamente.")
                self.add_rows(sheet, 500)
                self.append_values(sheet, start, data)
            else:
                raise

    @catch_and_log_errors
    def get_sheet_id(self, sheet: str) -> Optional[int]:
        if sheet in self._sheet_id_cache:
            return self._sheet_id_cache[sheet]
        meta = self.sheet.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta.get("sheets", []):
            if s["properties"]["title"] == sheet:
                sid = s["properties"]["sheetId"]
                self._sheet_id_cache[sheet] = sid
                return sid
        return None

    @catch_and_log_errors
    def batch_update(self, requests: List[Dict[str, Any]]) -> None:
        self.sheet.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": requests},
        ).execute()

    def update_cell_format(
        self,
        sheet: str,
        start_row: int, start_col: int, end_row: int, end_col: int,
        color: Dict[Literal["red", "green", "blue"], float],
    ) -> Dict[str, Any]:
        return {
            "repeatCell": {
                "range": {
                    "sheetId": self.get_sheet_id(sheet),
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col - 1,
                    "endColumnIndex": end_col,
                },
                "cell": {"userEnteredFormat": {"backgroundColor": color}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        }

    def merge_cells(self, sheet: str, start_row: int, start_col: int, end_row: int, end_col: int) -> Dict[str, Any]:
        return {
            "mergeCells": {
                "range": {
                    "sheetId": self.get_sheet_id(sheet),
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col - 1,
                    "endColumnIndex": end_col - 1,
                },
                "mergeType": "MERGE_ALL",
            }
        }

    def unmerge_cells(self, sheet: str, start_row: int, start_col: int, end_row: int, end_col: int) -> Dict[str, Any]:
        return {
            "unmergeCells": {
                "range": {
                    "sheetId": self.get_sheet_id(sheet),
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col - 1,
                    "endColumnIndex": end_col - 1,
                }
            }
        }

    @catch_and_log_errors
    def add_rows(self, sheet: str, count: int) -> None:
        self.batch_update([{
            "appendDimension": {
                "sheetId": self.get_sheet_id(sheet),
                "dimension": "ROWS",
                "length": count,
            }
        }])

    @catch_and_log_errors
    def get_range_of_sheet(self, sheet: str) -> str:
        vals = self.get_values(sheet, sheet)  # "sheet" sem intervalo -> aba inteira
        rows = len(vals)
        cols = len(vals[0]) if vals else 0
        return f"A1:{col_letter(cols)}{rows}" if rows and cols else "A1:A1"

    @catch_and_log_errors
    def load_sheet_as_df(self, sheet: str) -> pd.DataFrame:
        rng = self.get_range_of_sheet(sheet)
        vals = self.get_values(sheet, rng)
        if not vals:
            return pd.DataFrame()
        header, data = vals[0], vals[1:]
        data = [row + [""] * (len(header) - len(row)) for row in data]
        return pd.DataFrame(data, columns=header)

    @catch_and_log_errors
    def format_df_for_sheet(self, df: pd.DataFrame, sheet: str, rename_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        existing = self.load_sheet_as_df(sheet)
        if existing.empty:
            return df.rename(columns=rename_map or {})
        cols = existing.columns.tolist()
        df2 = df.copy()
        if rename_map:
            df2.rename(columns=rename_map, inplace=True)
        for c in cols:
            if c not in df2:
                df2[c] = ""
        return df2[cols]

    def _range_indices(self, range_: str):
        start, end = range_.split(":")
        return (
            int(start[1:]) - 1,  # startRowIndex
            int(end[1:]),        # endRowIndex
            ord(start[0].upper()) - ord("A"),  # startColumnIndex
            ord(end[0].upper()) - ord("A") + 1 # endColumnIndex
        )

    @catch_and_log_errors
    def insert_dropdown_list(self, sheet: str, range_: str, values: List[str], colors: Optional[Dict[str, Dict[str, float]]] = None):
        sid = self.get_sheet_id(sheet)
        srow, erow, scol, ecol = self._range_indices(range_)
        reqs = [{
            "setDataValidation": {
                "range": {"sheetId": sid, "startRowIndex": srow, "endRowIndex": erow, "startColumnIndex": scol, "endColumnIndex": ecol},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in values]},
                    "showCustomUi": True, "strict": True
                }
            }
        }]
        if colors:
            for value, color in colors.items():
                if value in values:
                    reqs.append({
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{"sheetId": sid, "startRowIndex": srow, "endRowIndex": erow, "startColumnIndex": scol, "endColumnIndex": ecol}],
                                "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": value}]},
                                                "format": {"backgroundColor": color}}
                            },
                            "index": 0
                        }
                    })
        self.batch_update(reqs)

    def add_dropdown_list(self, sheet: str, column_letter: str, values: List[str], colors: Optional[Dict[str, Dict[str, float]]] = None) -> None:
        last = self.get_last_filled_row(sheet, "A1:Z")
        rng = f"{column_letter}2:{column_letter}{max(last, 2)}"
        self.insert_dropdown_list(sheet, rng, values, colors)

    @catch_and_log_errors
    def update_row_by_index(self, sheet: str, index_1based: int, row_values: List[str]) -> None:
        cols = len(row_values)
        rng = f"A{index_1based}:{col_letter(cols)}{index_1based}"
        self.update_values(sheet, rng, [row_values])
