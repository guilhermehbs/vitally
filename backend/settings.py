import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', '').strip()
GOOGLE_SHEETS_WORKSHEET = os.getenv('GOOGLE_SHEETS_WORKSHEET', 'Pacientes')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

COLS = [
    'id','nome','telefone','email',
    'data_entrada','data_ultimo_pagamento','data_proxima_cobranca','ativo'
]

def _open_spreadsheet(gc, id_or_url: str):
    if not id_or_url:
        raise RuntimeError('Defina GOOGLE_SPREADSHEET_ID (ou a URL completa) no .env')
    if id_or_url.startswith('http'):
        return gc.open_by_url(id_or_url)
    return gc.open_by_key(id_or_url)

def get_ws():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    gc = gspread.authorize(creds)

    sh = _open_spreadsheet(gc, GOOGLE_SPREADSHEET_ID)

    try:
        ws = sh.worksheet(GOOGLE_SHEETS_WORKSHEET)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=GOOGLE_SHEETS_WORKSHEET, rows=1000, cols=len(COLS))

    headers = ws.row_values(1)
    if headers != COLS:
        ws.clear()
        ws.update('A1', [COLS])

    return ws
