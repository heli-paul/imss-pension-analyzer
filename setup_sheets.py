from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '1O5JC2VEjPBb_XzQUMxqYbRqHSOCON3r0F0jQcrGbrQw'
CREDENTIALS_PATH = '/home/heli_paul/imss-pension-analyzer/credentials.json'

def setup_sheet():
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    
    headers = [
        'Timestamp', 'Nombre Completo', 'CURP', 'NSS', 'RFC',
        'Fecha Nacimiento', 'Sexo', 'Entidad Federativa', 'Municipio',
        'Localidad', 'UMF', 'Fecha Vigencia Inicial', 'Fecha Vigencia Final',
        'Semanas Cotizadas', 'Última Fecha Actualización', 'Folio',
        'Fecha Emisión', 'Número Control', 'Nombre Archivo', 'Hash Archivo', 'Ruta Archivo'
    ]
    
    try:
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {'title': 'Constancias_IMSS_Completo'}
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=request_body
        ).execute()
        print("✅ Hoja creada")
    except:
        print("ℹ️  Hoja ya existe")
    
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Constancias_IMSS_Completo!A1:U1',
        valueInputOption='RAW',
        body={'values': [headers]}
    ).execute()
    
    print("✅ Configuración completada")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

if __name__ == '__main__':
    setup_sheet()


