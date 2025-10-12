# verify_credentials.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '1O5JC2VEjPBb_XzQUMxqYbRqHSOCON3r0F0jQcrGbrQw'
CREDENTIALS_PATH = '/home/heli_paul/imss-pension-analyzer/src/parser/credentials.json'

try:
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    
    # Intentar leer el spreadsheet
    result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    
    print("✅ Credenciales válidas")
    print(f"📊 Spreadsheet: {result.get('properties', {}).get('title')}")
    print(f"📄 Hojas disponibles:")
    for sheet in result.get('sheets', []):
        print(f"   - {sheet['properties']['title']}")
    
except Exception as e:
    print(f"❌ Error de credenciales: {e}")
