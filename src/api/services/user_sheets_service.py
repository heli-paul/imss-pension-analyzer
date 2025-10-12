from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class UserSheetsService:
    """Servicio para crear y gestionar Google Sheets individuales por usuario"""
    
    def __init__(self):
        # Buscar credentials
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'credentials.json'),
        ]
        
        self.credentials_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.credentials_path = path
                break
        
        self.service = None
        if self.credentials_path:
            self._initialize_service()
    
    def _initialize_service(self):
        """Inicializa el servicio de Google Sheets"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("✅ UserSheetsService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio: {e}")
    
    def crear_sheet_para_usuario(self, user_email: str, company_name: str = None):
        """
        Crea un Google Sheet nuevo para un usuario específico
        
        Returns:
            tuple: (spreadsheet_id, spreadsheet_url, success)
        """
        if not self.service:
            return None, None, False
        
        try:
            # Nombre del spreadsheet
            sheet_name = f"IMSS Analyzer - {company_name or user_email}"
            
            # Crear nuevo spreadsheet
            spreadsheet = {
                'properties': {
                    'title': sheet_name
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl')
            
            logger.info(f"✅ Sheet creado para {user_email}: {spreadsheet_id}")
            
            # Configurar la hoja con columnas
            self._configurar_hoja(spreadsheet_id)
            
            # Compartir con el usuario (opcional)
            self._compartir_con_usuario(spreadsheet_id, user_email)
            
            return spreadsheet_id, spreadsheet_url, True
            
        except Exception as e:
            logger.error(f"❌ Error creando sheet: {e}")
            return None, None, False
    
    def _configurar_hoja(self, spreadsheet_id: str):
        """Configura la hoja con los encabezados correctos"""
        try:
            # Renombrar Sheet1 a "Constancias_IMSS"
            requests = [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'title': 'Constancias_IMSS_Completo'
                    },
                    'fields': 'title'
                }
            }]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            # Agregar encabezados
            headers = [
                'Archivo', 'Fecha Consulta', 'NSS', 'CURP', 'Nombre',
                'Fecha de Nacimiento', 'Edad', 'Fecha de Emisión', 'Ley Aplicable',
                'Fecha Primer Alta', 'Semanas Cotizadas IMSS', 'Semanas Descontadas',
                'Total de Semanas Cotizadas', 'Semanas Reintegradas', 'Fecha Última Baja',
                'Fecha de Vencimiento', 'Salario Promedio Diario', 'Tiene 250 Semanas Completas',
                'Total de Días Calculados', 'Fecha Inicio Ventana', 'Fecha Fin Ventana'
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Constancias_IMSS_Completo!A1:U1',
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            
            # Formatear encabezados
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
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
            
            logger.info(f"✅ Hoja configurada con encabezados")
            
        except Exception as e:
            logger.error(f"❌ Error configurando hoja: {e}")
    
    def _compartir_con_usuario(self, spreadsheet_id: str, user_email: str):
        """Comparte el spreadsheet con el usuario (permisos de editor)"""
        try:
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': user_email
            }
            
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=True,
                emailMessage=f'Te compartimos tu calculadora personal de análisis IMSS. Aquí llegarán todos tus análisis de constancias.'
            ).execute()
            
            logger.info(f"✅ Sheet compartido con {user_email}")
            
        except Exception as e:
            logger.error(f"⚠️ No se pudo compartir con usuario: {e}")


