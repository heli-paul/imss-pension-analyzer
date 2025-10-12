# setup_sheets.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '1O5JC2VEjPBb_XzQUMxqYbRqHSOCON3r0F0jQcrGbrQw'
CREDENTIALS_PATH = '/home/heli_paul/imss-pension-analyzer/src/parser/credentials.json'

def setup_sheet():
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    
    # Columnas según tu parser
    headers = [
        'Timestamp',
        'Nombre Completo',
        'CURP',
        'NSS',
        'RFC',
        'Fecha Nacimiento',
        'Sexo',
        'Entidad Federativa',
        'Municipio',
        'Localidad',
        'UMF',
        'Fecha Vigencia Inicial',
        'Fecha Vigencia Final',
        'Semanas Cotizadas',
        'Última Fecha Actualización',
        'Folio',
        'Fecha Emisión',
        'Número Control',
        'Nombre Archivo',
        'Hash Archivo',
        'Ruta Archivo'
    ]
    
    try:
        # Intentar crear la hoja
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': 'Constancias_IMSS_Completo'
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=request_body
        ).execute()
        print("✅ Hoja 'Constancias_IMSS_Completo' creada")
    except Exception as e:
        print(f"ℹ️  Hoja ya existe o error: {e}")
    
    # Agregar encabezados
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Constancias_IMSS_Completo!A1:U1',
        valueInputOption='RAW',
        body={'values': [headers]}
    ).execute()
    
    # Formatear encabezados
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            'requests': [{
                'repeatCell': {
                    'range': {
                        'sheetId': get_sheet_id(service, 'Constancias_IMSS_Completo'),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86},
                            'textFormat': {
                                'bold': True,
                                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
        }
    ).execute()
    
    print("✅ Encabezados configurados con formato")
    print(f"📊 Total de columnas: {len(headers)}")

def get_sheet_id(service, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return 0

if __name__ == '__main__':
    setup_sheet()
