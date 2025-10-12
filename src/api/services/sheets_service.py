from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, spreadsheet_id: str = None):
        self.spreadsheet_id = spreadsheet_id or '1O5JC2VEjPBb_XzQUMxqYbRqHSOCON3r0F0jQcrGbrQw'
        
        # Buscar credentials.json
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
        self._initialize_service()
    
    def _initialize_service(self):
        """Inicializa el servicio de Google Sheets"""
        try:
            if not self.credentials_path:
                logger.error("❌ No se encontró credentials.json")
                return
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info(f"✅ GoogleSheetsManager inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando Google Sheets: {e}")
            self.service = None
    
    def _safe_get(self, obj, *keys, default=''):
        """Obtiene valores de forma segura de diccionarios anidados"""
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, default)
            else:
                return default
        return obj if obj is not None else default
    
    def agregar_constancia_completa(self, datos: dict, nombre_archivo: str = ""):
        """
        Agrega una fila con los datos según la estructura REAL del parser
        
        Columnas:
        1. Archivo
        2. Fecha Consulta
        3. NSS
        4. CURP
        5. Nombre
        6. Fecha de Nacimiento
        7. Edad
        8. Fecha de Emisión
        9. Ley Aplicable
        10. Fecha Primer Alta
        11. Semanas Cotizadas IMSS
        12. Semanas Descontadas
        13. Total de Semanas Cotizadas
        14. Semanas Reintegradas
        15. Fecha Última Baja
        16. Fecha de Vencimiento
        17. Salario Promedio Diario
        18. Tiene 250 Semanas Completas
        19. Total de Días Calculados
        20. Fecha Inicio Ventana
        21. Fecha Fin Ventana
        """
        if not self.service:
            return False, "Servicio de Google Sheets no inicializado"
        
        try:
            # Extraer secciones según estructura REAL
            datos_personales = datos.get('datos_personales', {})
            semanas_descontadas = datos.get('semanas_descontadas', {})
            conservacion = datos.get('conservacion_derechos', {})
            promedio_250 = datos.get('promedio_salarial_250_semanas', {})
            
            # 1. Archivo
            archivo = nombre_archivo
            
            # 2. Fecha Consulta
            fecha_consulta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 3. NSS
            nss = self._safe_get(datos_personales, 'nss')
            
            # 4. CURP
            curp = self._safe_get(datos_personales, 'curp')
            
            # 5. Nombre
            nombre = self._safe_get(datos_personales, 'nombre')
            
            # 6. Fecha de Nacimiento
            fecha_nacimiento = self._safe_get(datos_personales, 'fecha_nacimiento')
            
            # 7. Edad
            edad = self._safe_get(datos_personales, 'edad')
            
            # 8. Fecha de Emisión
            fecha_emision = self._safe_get(datos_personales, 'fecha_emision')
            
            # 9. Ley Aplicable
            ley_aplicable = self._safe_get(datos_personales, 'ley_aplicable')
            
            # 10. Fecha Primer Alta
            fecha_primer_alta = self._safe_get(datos_personales, 'fecha_primer_alta')
            
            # 11. Semanas Cotizadas IMSS
            semanas_imss = self._safe_get(datos_personales, 'semanas_cotizadas_imss')
            if not semanas_imss:
                semanas_imss = self._safe_get(semanas_descontadas, 'semanas_cotizadas_imss')
            
            # 12. Semanas Descontadas
            total_descontadas = self._safe_get(datos_personales, 'semanas_descontadas')
            if not total_descontadas:
                total_descontadas = self._safe_get(semanas_descontadas, 'semanas_descontadas')
            
            # 13. Total de Semanas Cotizadas
            total_semanas = self._safe_get(datos_personales, 'total_semanas_cotizadas')
            if not total_semanas:
                total_semanas = self._safe_get(semanas_descontadas, 'total_semanas_cotizadas')
            
            # 14. Semanas Reintegradas
            semanas_reintegradas = self._safe_get(datos_personales, 'semanas_reintegradas')
            if not semanas_reintegradas:
                semanas_reintegradas = self._safe_get(semanas_descontadas, 'semanas_reintegradas')
            
            # 15. Fecha Última Baja
            fecha_ultima_baja = self._safe_get(conservacion, 'fecha_ultima_baja')
            # Limpiar formato de fecha (eliminar T00:00:00)
            if fecha_ultima_baja and 'T' in str(fecha_ultima_baja):
                fecha_ultima_baja = str(fecha_ultima_baja).split('T')[0]
            
            # 16. Fecha de Vencimiento
            fecha_vencimiento = self._safe_get(conservacion, 'fecha_vencimiento')
            if fecha_vencimiento and 'T' in str(fecha_vencimiento):
                fecha_vencimiento = str(fecha_vencimiento).split('T')[0]
            
            # 17. Salario Promedio Diario
            salario_promedio = self._safe_get(promedio_250, 'salario_promedio_diario')
            
            # 18. Tiene 250 Semanas Completas
            tiene_250 = self._safe_get(promedio_250, 'tiene_250_semanas_completas')
            
            # 19. Total de Días Calculados
            total_dias = self._safe_get(promedio_250, 'total_dias_calculados')
            
            # 20. Fecha Inicio Ventana
            fecha_inicio_ventana = self._safe_get(promedio_250, 'fecha_inicio_ventana')
            if fecha_inicio_ventana and 'T' in str(fecha_inicio_ventana):
                fecha_inicio_ventana = str(fecha_inicio_ventana).split('T')[0]
            
            # 21. Fecha Fin Ventana
            fecha_fin_ventana = self._safe_get(promedio_250, 'fecha_fin_ventana')
            if fecha_fin_ventana and 'T' in str(fecha_fin_ventana):
                fecha_fin_ventana = str(fecha_fin_ventana).split('T')[0]
            
            # Preparar fila con 21 columnas
            row = [
                str(archivo),                    # 1
                str(fecha_consulta),             # 2
                str(nss),                        # 3
                str(curp),                       # 4
                str(nombre),                     # 5
                str(fecha_nacimiento),           # 6
                str(edad),                       # 7
                str(fecha_emision),              # 8
                str(ley_aplicable),              # 9
                str(fecha_primer_alta),          # 10
                str(semanas_imss),               # 11
                str(total_descontadas),          # 12
                str(total_semanas),              # 13
                str(semanas_reintegradas),       # 14
                str(fecha_ultima_baja),          # 15
                str(fecha_vencimiento),          # 16
                str(salario_promedio),           # 17
                str(tiene_250),                  # 18
                str(total_dias),                 # 19
                str(fecha_inicio_ventana),       # 20
                str(fecha_fin_ventana)           # 21
            ]
            
            # Log de datos extraídos
            logger.info(f"📊 Datos extraídos para Sheets:")
            logger.info(f"   - Archivo: {archivo}")
            logger.info(f"   - NSS: {nss}")
            logger.info(f"   - Nombre: {nombre}")
            logger.info(f"   - Semanas IMSS: {semanas_imss}")
            logger.info(f"   - Total Semanas: {total_semanas}")
            logger.info(f"   - Salario Promedio: {salario_promedio}")
            logger.info(f"   - Tiene 250 Semanas: {tiene_250}")
            
            body = {'values': [row]}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Constancias_IMSS_Completo!A:U',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_rows = result.get('updates', {}).get('updatedRows', 0)
            logger.info(f"✅ Datos enviados a Google Sheets: {updated_rows} fila(s)")
            
            return True, f"Datos enviados correctamente ({updated_rows} fila)"
            
        except Exception as e:
            error_msg = f"Error enviando a Google Sheets: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            return False, error_msg


