import os, csv, re, socket, logging, pandas as pd
from typing import List, Dict, Optional, Any, Callable, Literal, Mapping

from functools import wraps
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials as SA


def catch_and_log_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as err:
            logging.error(f'Erro no metodo {func.__name__}: {err}')
            return None
        except Exception as e:
            logging.error(f'Erro inesperado em {func.__name__}: {e}')
            return None
    return wrapper


class GoogleSheetsHandler:
    def __init__(self, spreadsheet_id: str, test_mode: bool = False) -> None:
        self.spreadsheet_id = spreadsheet_id
        socket.setdefaulttimeout(300)
        self._sheet_id_cache: Dict[str, int] = {}
        self.sheet = None

        if not test_mode:
            self.sheet = self._build_service()

    @catch_and_log_errors
    def _build_service(self) -> Optional[Any]:
        cred_path = self._fetch_credentials()
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = SA.from_service_account_file(cred_path, scopes=scopes)
        return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

    @catch_and_log_errors
    def _fetch_credentials(self) -> Optional[str]:
        path = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        if not os.path.isfile(path):
            raise FileNotFoundError(f'Credenciais não encontradas em: {path}')
        return path

    @staticmethod
    def _read_csv_file(filepath: str) -> List[List[str]]:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            data = list(csv.reader(csvfile))
        if not data:
            return []
        logging.info('CSV data read successfully')
        return data[1:]

    def read_data_from_file(self, filename: str) -> List[List[str]]:
        return self._read_csv_file(filename)

    @staticmethod
    def _normalize_data(df: pd.DataFrame) -> List[List[str]]:
        if df.index.name is not None or df.index.dtype != 'int64':
            df = df.reset_index(drop=True)
        return [list(map(str, row))[1:] for row in df.itertuples()]

    def _range(self, sheet: str, cell_range: str) -> str:
        return f'{sheet}!{cell_range}'

    def _ensure_client(self) -> None:
        if self.sheet is None:
            raise RuntimeError('Cliente Google Sheets não inicializado (test_mode=True?).')


    @catch_and_log_errors
    def add_data_to_sheet(self, df: pd.DataFrame, sheet: str) -> None:
        self._ensure_client()
        if not isinstance(df, pd.DataFrame):
            raise TypeError('Df deve ser um DataFrame')
        last_line = self.get_last_filled_row(sheet=sheet, cell_range='A1:Z')
        last_line = last_line or 0
        start_row = 2 if last_line == 0 else last_line + 1
        limit = f'A{start_row}'
        data = self._normalize_data(df=df)
        try:
            self._insert_data(data=data, sheet=sheet, cell_range=limit)
        except HttpError as e:
            if 'exceeds grid limits' in str(e):
                logging.warning('Limite de linhas excedido, adicionando mais linhas')
                self.add_rows(sheet=sheet, count=10)
                self._insert_data(data=data, sheet=sheet, cell_range=limit)
            else:
                raise

    @catch_and_log_errors
    def _insert_data(
        self,
        data: Optional[List[List[str]]] = None,
        sheet: Optional[str] = None,
        cell_range: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> None:
        self._ensure_client()
        if not sheet or not (data or filename):
            raise ValueError('sheet ou dados/arquivo não foram informados')

        target_range = self._range(sheet=sheet, cell_range=cell_range or 'A1')

        if filename:
            data = self.read_data_from_file(filename=filename)

        if not data:
            logging.info('Nenhum dado para inserir.')
            return

        self.sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=target_range,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': data},
        ).execute()

        logging.info('Data inserted successfully')

    @catch_and_log_errors
    def delete_range(self, sheet: str, cell_range: str) -> None:
        self._ensure_client()
        self.sheet.values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
        ).execute()
        logging.info('Data cleared successfully')

    @catch_and_log_errors
    def get_last_filled_row(self, sheet: str, cell_range: str) -> int:
        self._ensure_client()
        values = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=self._range(sheet, cell_range),
        ).execute().get('values', [])
        return max((i + 1 for i, row in enumerate(values) if any(str(cell).strip() for cell in row)), default=0)

    @catch_and_log_errors
    def get_sheet_id(self, sheet: str) -> Optional[int]:
        self._ensure_client()
        if sheet in self._sheet_id_cache:
            return self._sheet_id_cache[sheet]

        sheets = self.sheet.get(spreadsheetId=self.spreadsheet_id).execute().get('sheets', [])
        for s in sheets:
            if s['properties']['title'] == sheet:
                sheet_id = s.get('properties', {}).get('sheetId')
                if sheet_id is not None:
                    self._sheet_id_cache[sheet] = sheet_id
                return sheet_id
        return None

    @catch_and_log_errors
    def get_all_values_of_column(self, sheet: str, column_letter: str) -> List[str]:
        self._ensure_client()
        range_col = f'{sheet}!{column_letter}:{column_letter}'
        values = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_col,
        ).execute().get('values', [])
        return [row[0] for row in values[1:] if row] if len(values) > 1 else []

    def update_cell_format(
        self,
        sheet: str,
        start_row: int,
        start_col: int,
        end_row: int,
        end_col: int,
        color: Dict[Literal['red', 'green', 'blue'], float],
    ) -> Dict:
        return {
            'updateCells': {
                'range': {
                    'sheetId': self.get_sheet_id(sheet),
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col,
                },
                'rows': [{'values': [{'userEnteredFormat': {'backgroundColor': color}}]}] * max(end_row - start_row, 1),
                'fields': 'userEnteredFormat.backgroundColor',
            }
        }

    def merge_cells(self, sheet: str, start_row: int, start_col: int, end_row: int, end_col: int) -> Dict:
        return {
            'mergeCells': {
                'range': {
                    'sheetId': self.get_sheet_id(sheet),
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col,
                },
                'mergeType': 'MERGE_ALL',
            }
        }

    def unmerge_cells(self, sheet: str, start_row: int, start_col: int, end_row: int, end_col: int) -> Dict:
        return {
            'unmergeCells': {
                'range': {
                    'sheetId': self.get_sheet_id(sheet),
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col,
                }
            }
        }

    @catch_and_log_errors
    def batch_update(self, requests: List[Dict]) -> None:
        self._ensure_client()
        if not requests:
            return
        self.sheet.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests},
        ).execute()

    @catch_and_log_errors
    def add_rows(self, sheet: str, count: int) -> None:
        self._ensure_client()
        self.sheet.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                'requests': [
                    {
                        'appendDimension': {
                            'sheetId': self.get_sheet_id(sheet),
                            'dimension': 'ROWS',
                            'length': count,
                        }
                    }
                ]
            },
        ).execute()
        logging.info(f'{count} rows added to {sheet}')

    @catch_and_log_errors
    def get_range_of_sheet(self, sheet: str) -> str:
        self._ensure_client()
        values = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=sheet,
        ).execute().get('values', [])

        rows = len(values)
        cols = len(values[0]) if values else 0

        def col_letter(n: int) -> str:
            res = ''
            while n:
                n, r = divmod(n - 1, 26)
                res = chr(65 + r) + res
            return res

        if rows == 0 or cols == 0:
            return 'A1:A1'

        return f'A1:{col_letter(cols)}{rows}'

    @catch_and_log_errors
    def load_sheet_as_df(self, sheet: str) -> pd.DataFrame:
        self._ensure_client()
        data_range = self.get_range_of_sheet(sheet)
        values = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f'{sheet}!{data_range}',
        ).execute().get('values', [])

        if not values:
            return pd.DataFrame()

        width = len(values[0])
        for row in values[1:]:
            if len(row) < width:
                row.extend([''] * (width - len(row)))

        return pd.DataFrame(values[1:], columns=values[0])

    @catch_and_log_errors
    def format_df_for_sheet(self, df: pd.DataFrame, sheet: str, rename_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        existing = self.load_sheet_as_df(sheet) or pd.DataFrame()
        columns = existing.columns.tolist()
        if not columns:
            df_copy = df.copy()
            if rename_map:
                df_copy.rename(columns=rename_map, inplace=True)
            return df_copy

        df_copy = df.copy()
        if rename_map:
            df_copy.rename(columns=rename_map, inplace=True)
        for col in columns:
            if col not in df_copy:
                df_copy[col] = ''
        return df_copy[columns]

    def _col_to_idx(self, col: str) -> int:
        col = col.upper()
        n = 0
        for ch in col:
            n = n * 26 + (ord(ch) - ord('A') + 1)
        return n - 1
    
    def _col_to_letter(self, n: int) -> str:
        if n <= 0:
            raise ValueError("n deve ser >= 1")
        res = ""
        while n:
            n, r = divmod(n - 1, 26)
            res = chr(65 + r) + res
        return res

    @catch_and_log_errors
    def update_row_by_index(
        self,
        sheet: str,
        row_index_1based: int,
        values: List[str],
        value_input_option: str = "USER_ENTERED",
    ) -> None:
        self._ensure_client()
        if row_index_1based < 1:
            raise ValueError("row_index_1based deve ser >= 1")
        if not values:
            return

        last_col_letter = self._col_to_letter(len(values))
        target_range = f"{sheet}!A{row_index_1based}:{last_col_letter}{row_index_1based}"

        try:
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=target_range,
                valueInputOption=value_input_option,
                body={"values": [values]},
            ).execute()
            logging.info(f"Linha {row_index_1based} atualizada em {sheet}")
        except HttpError as e:
            if "exceeds grid limits" in str(e):
                logging.warning("Limite de linhas excedido; adicionando mais linhas e tentando novamente.")
                self.add_rows(sheet=sheet, count=1000)
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=target_range,
                    valueInputOption=value_input_option,
                    body={"values": [values]},
                ).execute()
                logging.info(f"Linha {row_index_1based} atualizada após expandir grade em {sheet}")
            else:
                raise

    def get_range_indices(self, range_: str):
        start, end = range_.split(':')
        m1 = re.match(r'([A-Za-z]+)(\d+)', start)
        m2 = re.match(r'([A-Za-z]+)(\d+)', end)
        if not m1 or not m2:
            raise ValueError(f'Range inválido: {range_}')

        scol, srow = m1.group(1), int(m1.group(2))
        ecol, erow = m2.group(1), int(m2.group(2))

        return (
            srow - 1,
            erow,
            self._col_to_idx(scol),
            self._col_to_idx(ecol) + 1,
        )

    @catch_and_log_errors
    def _insert_dropdown_list(
        self,
        sheet: str,
        range_: str,
        values: List[str],
        colors: Optional[Mapping[str, Dict[str, float]]] = None,
    ):
        self._ensure_client()
        sheet_id = self.get_sheet_id(sheet=sheet)
        start_row, end_row, start_col, end_col = self.get_range_indices(range_)

        requests: List[Dict[str, Any]] = [{
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col,
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [{'userEnteredValue': v} for v in values],
                    },
                    'showCustomUi': True,
                    'strict': True,
                },
            }
        }]

        if colors:
            for value, color in colors.items():
                if value in values:
                    requests.append({
                        'addConditionalFormatRule': {
                            'rule': {
                                'ranges': [{
                                    'sheetId': sheet_id,
                                    'startRowIndex': start_row,
                                    'endRowIndex': end_row,
                                    'startColumnIndex': start_col,
                                    'endColumnIndex': end_col,
                                }],
                                'booleanRule': {
                                    'condition': {
                                        'type': 'TEXT_EQ',
                                        'values': [{'userEnteredValue': value}],
                                    },
                                    'format': {'backgroundColor': color},
                                },
                            },
                            'index': 0,
                        }
                    })

        self.sheet.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests},
        ).execute()

    def add_dropdown_list(
        self,
        sheet: str,
        values: List[str],
        colors: Optional[Mapping[str, Dict[str, float]]],
        column_letter: str,
    ) -> None:
        last_line = self.get_last_filled_row(sheet=sheet, cell_range='A1:Z') or 1
        end_row = max(last_line, 2)
        range_dropdown = f'{column_letter}2:{column_letter}{end_row}'
        self._insert_dropdown_list(sheet=sheet, range_=range_dropdown, values=values, colors=colors)
