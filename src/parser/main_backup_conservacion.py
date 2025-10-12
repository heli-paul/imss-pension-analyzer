"""
Parser IMSS con conservación de derechos - Versión Modular
Módulo 1: Extracción de datos básicos
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
import pdfplumber
import io
import json
import os
import shutil
from modules.modulo3 import PensionProcessor, procesar_pension_imss
from datetime import datetime
from correccion_semanas import procesar_con_correcciones
from correccion_semanas_final import aplicar_correccion_exacta
import logging
import gspread
from google.oauth2.service_account import Credentials

# Importar nuestro módulo de extracción básica
from modules.basic_extractor import extract_basic_data_from_pdf
from modules.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def procesar_constancia_completa(texto_pdf: str, con_correcciones: bool = True, debug: bool = False) -> dict:
    """
    Función principal con correcciones integradas
    """
    # Tu código actual (que ya funciona y da 1124)
    from historial_laboral import HistorialLaboralExtractor  # ajusta la ruta según tu import actual
    
    analizador = HistorialLaboralExtractor()
    resultado_base = analizador.procesar_constancia(texto_pdf)
    resultado = aplicar_correccion_exacta(resultado_base)
    
    if not con_correcciones:
        return resultado_original
    
    # Aplicar correcciones post-extracción
    resultado_corregido = procesar_con_correcciones(resultado_original, modo_debug=debug)
    
    if debug:
        m = resultado_corregido['metricas_correccion']
        print("=" * 60)
        print("CORRECCIÓN COMPLETA APLICADA")
        print("=" * 60)
        print(f"Semanas con períodos vigentes corregidos: {m['semanas_parser_original']}")
        print(f"Semanas sin redondeo: {m['semanas_sin_redondeo']}")
        print(f"Semanas sin empalmes: {m['semanas_sin_empalmes']}")
        print(f"Semanas IMSS oficial: {m['semanas_imss_oficial']}")
        print(f"Precisión final: ±{m['precision_final']} semanas")
        print(f"Mejora total: {m['mejora_absoluta']} semanas ({m['mejora_porcentual']}%)")
        print(f"Empalmes detectados y corregidos: {m['empalmes_detectados']}")
        print("=" * 60)
    
    return resultado_corregido

# Función temporal para validación (se moverá al módulo 2)
def validar_constancia(data):
    return {"score_calidad": 95}

class GoogleSheetsManager:
    """Manejo completo de Google Sheets para constancias IMSS"""

    def __init__(self, credentials_file, spreadsheet_id):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._connect()

    def _connect(self):
        """Conectar con Google Sheets usando service account"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )

            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info("✅ Conexión exitosa con Google Sheets")

        except Exception as e:
            logger.error(f"❌ Error conectando con Google Sheets: {e}")
            raise

    def crear_hoja_si_no_existe(self, nombre_hoja):
        """Crear hoja si no existe y configurar headers"""
        try:
            try:
                worksheet = self.spreadsheet.worksheet(nombre_hoja)
                logger.info(f"✅ Hoja '{nombre_hoja}' ya existe")
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=nombre_hoja, rows=1000, cols=25
                )
                logger.info(f"✅ Hoja '{nombre_hoja}' creada")

                # Headers solo para datos básicos (Módulo 1)
                headers = [
                    'Fecha Procesamiento', 'Archivo', 'Nombre Cliente', 'NSS', 'CURP',
                    'Fecha Emisión', 'Semanas Cotizadas', 'Semanas IMSS', 'Semanas Descontadas',
                    'Semanas Reintegradas', 'Total Semanas', 'Ley Aplicable',
                    'Fecha Primer Alta', 'Años Antes 1997', 'Errores'
                ]

                worksheet.append_row(headers)

        except Exception as e:
            logger.error(f"❌ Error creando/accediendo hoja '{nombre_hoja}': {e}")

    def agregar_fila(self, nombre_hoja, datos):
        """Agregar fila de datos a la hoja"""
        try:
            worksheet = self.spreadsheet.worksheet(nombre_hoja)
            worksheet.append_row(datos)
            logger.info(f"✅ Fila agregada a '{nombre_hoja}'")
        except Exception as e:
            logger.error(f"❌ Error agregando fila a '{nombre_hoja}': {e}")

    def obtener_estadisticas_sheet(self, nombre_hoja="Constancias_IMSS_Basico"):
        """Obtener estadísticas del sheet"""
        try:
            worksheet = self.spreadsheet.worksheet(nombre_hoja)
            datos = worksheet.get_all_records()
            total = len(datos)

            return {
                "total": total,
                "mensaje": f"Google Sheets conectado - {total} constancias procesadas (solo datos básicos)"
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"total": 0, "mensaje": f"Error: {str(e)}"}

class DataStorage:
    def __init__(self):
        self.constancias_procesadas = []

    def agregar_constancia_basica(self, datos):
        """Procesar y almacenar datos básicos de constancia IMSS"""

        registro = {
            'fecha_procesamiento': datos.get('fecha_procesamiento', ''),
            'archivo': datos.get('archivo', ''),
            'nombre_cliente': datos.get('nombre', ''),
            'nss': datos.get('nss', ''),
            'curp': datos.get('curp', ''),
            'fecha_emision': datos.get('fecha_emision', ''),
            'semanas_cotizadas': datos.get('semanas_cotizadas', 0),
            'semanas_imss': datos.get('semanas_imss', 0),
            'semanas_descontadas': datos.get('semanas_descontadas', 0),
            'semanas_reintegradas': datos.get('semanas_reintegradas', 0),
            'total_semanas': datos.get('total_semanas', 0),
            'ley_aplicable': datos.get('ley_aplicable', 'indeterminado'),
            'fecha_primer_alta': datos.get('fecha_primer_alta', ''),
            'anos_cotizando_antes_1997': datos.get('anos_cotizando_antes_1997', 0),
            'errores': '; '.join(datos.get('errors', []))
        }

        self.constancias_procesadas.append(registro)

        # Enviar a Google Sheets
        if sheets_manager:
            self.enviar_datos_basicos_a_sheets(registro)

        return registro

    def enviar_datos_basicos_a_sheets(self, registro):
        """Enviar solo datos básicos a Google Sheets"""
        try:
            nombre_hoja = "Constancias_IMSS_Basico"
            sheets_manager.crear_hoja_si_no_existe(nombre_hoja)

            fila_datos = [
                registro['fecha_procesamiento'],
                registro['archivo'],
                registro['nombre_cliente'],
                registro['nss'],
                registro['curp'],
                registro['fecha_emision'],
                registro['semanas_cotizadas'],
                registro['semanas_imss'],
                registro['semanas_descontadas'],
                registro['semanas_reintegradas'],
                registro['total_semanas'],
                registro['ley_aplicable'],
                registro['fecha_primer_alta'],
                registro['anos_cotizando_antes_1997'],
                registro['errores']
            ]

            sheets_manager.agregar_fila(nombre_hoja, fila_datos)
            logger.info(f"✅ Datos básicos enviados a Google Sheets: NSS={registro['nss']}")

        except Exception as e:
            logger.error(f"❌ Error enviando datos básicos a Google Sheets: {e}")

# Configuración de FastAPI
app = FastAPI(
    title="IMSS Parser API - Módulo Básico",
    description="Parser con extracción de datos básicos únicamente",
    version="3.0.0"
)

# Configuración de Google Sheets
CREDENTIALS_FILE = "/home/heli_paul/imss-pension-analyzer/src/parser/credentials.json"
SPREADSHEET_ID = "1PGb0makALNm_nLlwl6gdu3ecv9gbJcY7JC9uHHq5mrk"

# Inicializar Google Sheets
try:
    sheets_manager = GoogleSheetsManager(CREDENTIALS_FILE, SPREADSHEET_ID)
    logger.info("✅ Google Sheets configurado en startup")
except Exception as e:
    logger.warning(f"Google Sheets no configurado: {e}")
    sheets_manager = None

data_storage = DataStorage()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IMSS Parser - Módulo Básico",
        "version": "3.0.0",
        "modulo": "Extracción de datos básicos únicamente",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_statistics():
    """Obtener estadísticas de las constancias procesadas"""
    if sheets_manager:
        stats = sheets_manager.obtener_estadisticas_sheet()
        return stats
    else:
        return {"error": "Google Sheets no configurado"}

@app.post("/parse/basic")
async def parse_basic_data_endpoint(file: UploadFile = File(...)):
    """
    Endpoint para extraer SOLO datos básicos del PDF
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    try:
        # Guardar archivo temporalmente
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extraer texto del PDF
        with pdfplumber.open(temp_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        # Usar el nuevo módulo para extraer datos básicos
        datos_basicos = extract_basic_data_from_pdf(full_text, file.filename)

        # Validación temporal
        validacion = validar_constancia(datos_basicos)
        datos_basicos["validacion"] = validacion

        # Almacenar datos básicos
        registro = data_storage.agregar_constancia_basica(datos_basicos)

        return {
            "modulo": "Datos Básicos",
            "datos": datos_basicos,
            "mensaje": "Extracción de datos básicos completada exitosamente"
        }

    except Exception as e:
        logger.error(f"Error parseando PDF {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parseando PDF: {str(e)}")

    finally:
        try:
            os.remove(temp_path)
        except:
            pass

@app.post("/debug/texto")
async def debug_texto_pdf(file: UploadFile = File(...)):
    """Ver el texto extraído del PDF"""
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    with pdfplumber.open(temp_path) as pdf:
        texto_completo = ""
        for i, page in enumerate(pdf.pages):
            texto_pagina = page.extract_text() or ""
            texto_completo += f"\n--- PÁGINA {i+1} ---\n{texto_pagina}"

    os.remove(temp_path)

    return {
        "texto_completo": texto_completo,
        "numero_paginas": len(pdf.pages),
        "longitud_total": len(texto_completo)
    }

@app.post("/parse/historial")
async def parse_historial_laboral(file: UploadFile = File(...)):
    """Procesar PDF para extraer historial laboral - VERSION CORREGIDA CON POST-PROCESAMIENTO"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo archivos PDF")

    temp_path = None
    try:
        # Guardar archivo temporal
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extraer texto
        with pdfplumber.open(temp_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        # PASO 1: Extracción base con tu parser existente
        from modules.modulo2.historial_laboral import HistorialLaboralExtractor
        extractor = HistorialLaboralExtractor()
        
        # Procesar con tu parser actual
        resultado_base = extractor.procesar_constancia(full_text)
        
        # PASO 2: Aplicar corrección post-procesamiento para exactitud perfecta
        resultado_final = aplicar_correccion_exacta(resultado_base)

        # Agregar información adicional
        resultado_final["archivo"] = file.filename
        
        return resultado_final

    except Exception as e:
        logger.error(f"Error procesando {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except:
                pass

@app.post("/parse/test-extraccion")
async def test_extraccion(file: UploadFile = File(...)):
    """Endpoint de prueba para verificar extracción de nombres"""
    temp_path = None
    try:
        # Guardar archivo temporal
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extraer texto del PDF
        with pdfplumber.open(temp_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

        from modules.modulo2.historial_laboral import HistorialLaboralExtractor
        extractor = HistorialLaboralExtractor()

        # Debug primero
        debug_info = extractor.debug_extraccion(full_text)

        # Extracción
        periodos = extractor.extraer_periodos(full_text)

        return {
            "debug": debug_info,
            "periodos": [p.to_dict() for p in periodos[:3]]  # Solo primeros 3
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except:
                pass
@app.post("/api/analizar-debug")
async def analizar_constancia_debug(pdf: UploadFile = File(...)):
    """Endpoint para analizar constancia IMSS con información de debug detallada"""
    
    try:
        # Validar que es un PDF
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
        
        # Leer el contenido del archivo
        pdf_content = await pdf.read()
        
        # Extraer texto del PDF
        texto_completo = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf_doc:
            for page_num, page in enumerate(pdf_doc.pages):
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo += f"\n--- PÁGINA {page_num + 1} ---\n"
                    texto_completo += texto_pagina + "\n"
        
        # Crear instancia del analizador
        analizador = HistorialLaboralExtractor()
        
        # Procesar con debug
        resultado = analizador.procesar_constancia_con_debug(texto_completo)
        
        return {
            "success": True,
            "mensaje": "Constancia procesada con debug exitosamente",
            "archivo": pdf.filename,
            "data": resultado
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando la constancia: {str(e)}"
        )
# Agregar este endpoint a tu FastAPI app existente
@app.post("/calculate/pension")
async def calculate_pension(file: UploadFile = File(...), debug_mode: bool = False):
    """
    Endpoint para cálculo completo de pensión IMSS
    Procesa el PDF y calcula promedio 250 semanas + conservación de derechos
    """
    try:
        # 1. Procesar historial laboral (usando tu parser existente)
        contents = await file.read()
        
        # Usar tu extractor existente para obtener datos completos
        extractor = HistorialLaboralExtractor()  # Tu clase existente
        resultado_parser = extractor.procesar_archivo_completo(contents, file.filename)
        
        # 2. Procesar con el Módulo 3
        processor = PensionProcessor(debug_mode=debug_mode)
        resultado_pension = processor.procesar_pension_completa(resultado_parser)
        
        # 3. Guardar en Google Sheets si es exitoso
        if resultado_pension.get('exito', False):
            try:
                # Preparar datos para sheets
                datos_sheets = {
                    'timestamp': resultado_pension['fecha_procesamiento'],
                    'archivo': file.filename,
                    'nombre': resultado_pension['asegurado']['nombre'],
                    'nss': resultado_pension['asegurado']['nss'],
                    'ley_aplicable': resultado_parser['datos_basicos']['ley_aplicable'],
                    'calidad_extraccion': resultado_pension['quality_assessment']['calidad_extraccion'],
                    'score_final': resultado_pension['calidad_final']['score_final'],
                    'nivel_calidad': resultado_pension['calidad_final']['nivel_calidad'],
                    'salario_promedio_250': resultado_pension['ruta_1_promedio_250_semanas'].get('salario_promedio_diario', 0),
                    'conservacion_dias': resultado_pension['ruta_2_conservacion_derechos']['calculo_conservacion'].get('dias_conservacion', 0),
                    'estado_derechos': resultado_pension['ruta_2_conservacion_derechos']['estado_derechos']['estado'],
                    'errores': len(resultado_pension['calidad_final']['resumen_alertas']['errores_criticos']),
                    'alertas': len(resultado_pension['calidad_final']['resumen_alertas']['alertas_revision'])
                }
                
                # Agregar a Google Sheets usando tu función existente
                agregar_a_sheets(datos_sheets)
                
            except Exception as e:
                print(f"Error guardando en sheets: {e}")
                # No fallar todo el proceso por error en sheets
        
        return resultado_pension
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error procesando pensión: {str(e)}",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# Endpoint adicional para testing con JSON directo
@app.post("/calculate/pension-from-json")
async def calculate_pension_from_json(pension_data: dict, debug_mode: bool = False):
    """
    Endpoint para testing - recibe JSON del parser directamente
    """
    try:
        processor = PensionProcessor(debug_mode=debug_mode)
        resultado = processor.procesar_pension_completa(pension_data)
        return resultado
        
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error procesando JSON: {str(e)}",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


