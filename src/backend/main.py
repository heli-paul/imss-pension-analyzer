"""
Backend mejorado con análisis pensionario completo
Integra parser mejorado + cálculos de pensión + Google Sheets
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
import gspread
from datetime import datetime, timedelta
import os
import logging
from typing import Optional, List, Dict, Any
import json
from decimal import Decimal, ROUND_HALF_UP

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IMSS Analysis Backend",
    description="Backend completo para análisis pensionario IMSS",
    version="2.0.0"
)

# Configuración desde variables de entorno
PARSER_URL = os.getenv("PARSER_URL", "http://localhost:8001/parse")
SHEETS_CREDS_PATH = os.getenv("SHEETS_CREDS_PATH", "")
GDRIVE_SHEET_ID = os.getenv("GDRIVE_SHEET_ID", "")
GDRIVE_SHEET_TAB = os.getenv("GDRIVE_SHEET_TAB", "Registros")

# Modelos de datos mejorados
class PeriodoLaboral(BaseModel):
    empresa: str
    registro_patronal: str
    entidad_federativa: str
    fecha_alta: str
    fecha_baja: Optional[str]
    salario_base: float
    vigente: bool
    dias_laborados: Optional[int] = 0
    semanas_cotizadas: Optional[float] = 0

class AnalisisPensionario(BaseModel):
    salario_promedio_250_semanas: float
    conservacion_derechos: bool
    ley_aplicable: str  # "73" o "97"
    pension_estimada_ley73: Optional[float] = None
    pension_estimada_ley97: Optional[float] = None
    modalidad_40_viable: bool
    costo_modalidad_40_mensual: Optional[float] = None
    beneficio_modalidad_40: Optional[float] = None
    años_faltantes_pension: Optional[int] = None

class ProyeccionAfore(BaseModel):
    saldo_estimado_actual: float
    pension_mensual_estimada: float
    pension_garantizada: float
    edad_retiro_estimada: int
    recomendacion: str

class ResultadoCompleto(BaseModel):
    # Datos básicos del parsing
    archivo: str
    nss: Optional[str]
    curp: Optional[str] 
    nombre: Optional[str]
    fecha_emision: Optional[str]
    semanas_cotizadas: Optional[int]
    semanas_imss: Optional[int]
    semanas_descontadas: Optional[int]
    semanas_reintegradas: Optional[int]
    
    # Períodos laborales
    periodos_laborales: List[PeriodoLaboral]
    
    # Análisis pensionario
    analisis_pensionario: AnalisisPensionario
    
    # Proyección AFORE
    proyeccion_afore: ProyeccionAfore
    
    # Metadatos
    timestamp: str
    costo_analisis: float = 20.0
    errors: List[str] = []

class IMSSAnalyzer:
    def __init__(self):
        self.uma_2024 = 108.57  # UMA vigente 2024
        self.salario_minimo_2024 = 248.93
        self.pension_garantizada_2024 = self.salario_minimo_2024 * 30.44
        
    def analizar_constancia(self, parsed_data: Dict, fecha_nacimiento: Optional[str] = None) -> ResultadoCompleto:
        """Análisis completo de constancia IMSS"""
        
        # Convertir períodos laborales
        periodos = []
        for p in parsed_data.get('periodos_laborales', []):
            periodo = PeriodoLaboral(**p)
            # Calcular días y semanas laborados
            if periodo.fecha_alta:
                fecha_inicio = datetime.strptime(periodo.fecha_alta, '%Y-%m-%d')
                if periodo.fecha_baja:
                    fecha_fin = datetime.strptime(periodo.fecha_baja, '%Y-%m-%d')
                else:
                    fecha_fin = datetime.now()
                
                dias = (fecha_fin - fecha_inicio).days + 1
                periodo.dias_laborados = dias
                periodo.semanas_cotizadas = round(dias / 7, 2)
            
            periodos.append(periodo)
        
        # Realizar análisis pensionario
        analisis = self._analizar_pension(parsed_data, periodos, fecha_nacimiento)
        
        # Realizar proyección AFORE
        proyeccion = self._proyectar_afore(parsed_data, periodos, fecha_nacimiento)
        
        # Crear resultado completo
        resultado = ResultadoCompleto(
            archivo=parsed_data.get('archivo', ''),
            nss=parsed_data.get('nss'),
            curp=parsed_data.get('curp'),
            nombre=parsed_data.get('nombre'),
            fecha_emision=parsed_data.get('fecha_emision'),
            semanas_cotizadas=parsed_data.get('semanas_cotizadas'),
            semanas_imss=parsed_data.get('semanas_imss'),
            semanas_descontadas=parsed_data.get('semanas_descontadas'),
            semanas_reintegradas=parsed_data.get('semanas_reintegradas'),
            periodos_laborales=periodos,
            analisis_pensionario=analisis,
            proyeccion_afore=proyeccion,
            timestamp=datetime.now().isoformat(),
            errors=parsed_data.get('errors', [])
        )
        
        return resultado
    
    def _analizar_pension(self, data: Dict, periodos: List[PeriodoLaboral], fecha_nacimiento: Optional[str]) -> AnalisisPensionario:
        """Análisis pensionario completo"""
        
        semanas_totales = data.get('semanas_cotizadas', 0) or 0
        
        # Calcular salario promedio últimas 250 semanas
        salario_promedio = self._calcular_salario_promedio_250_semanas(periodos, data.get('fecha_emision'))
        
        # Determinar conservación de derechos
        conservacion_derechos = semanas_totales >= 750
        
        # Determinar ley aplicable
        ley_aplicable = "97"  # Por defecto Ley 97
        if fecha_nacimiento and conservacion_derechos:
            nac_date = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
            if nac_date < datetime(1997, 7, 1):
                ley_aplicable = "73"
        
        # Cálculos de pensión
        pension_ley73 = None
        pension_ley97 = None
        
        if ley_aplicable == "73" and semanas_totales >= 500:
            pension_ley73 = self._calcular_pension_ley73(semanas_totales, salario_promedio)
        
        if semanas_totales >= 1250:  # 25 años para Ley 97
            pension_ley97 = self._calcular_pension_ley97(semanas_totales, salario_promedio, periodos)
        
        # Análisis Modalidad 40
        modalidad_40_viable = semanas_totales >= 52 and conservacion_derechos
        costo_m40 = None
        beneficio_m40 = None
        
        if modalidad_40_viable and salario_promedio > 0:
            costo_m40 = self._calcular_costo_modalidad40(salario_promedio)
            beneficio_m40 = self._calcular_beneficio_modalidad40(salario_promedio, semanas_totales)
        
        # Años faltantes para pensión
        años_faltantes = None
        if semanas_totales < 1250:  # Mínimo para pensión
            años_faltantes = max(0, (1250 - semanas_totales) / 52)
        
        return AnalisisPensionario(
            salario_promedio_250_semanas=salario_promedio,
            conservacion_derechos=conservacion_derechos,
            ley_aplicable=ley_aplicable,
            pension_estimada_ley73=pension_ley73,
            pension_estimada_ley97=pension_ley97,
            modalidad_40_viable=modalidad_40_viable,
            costo_modalidad_40_mensual=costo_m40,
            beneficio_modalidad_40=beneficio_m40,
            años_faltantes_pension=round(años_faltantes, 1) if años_faltantes else None
        )
    
    def _calcular_salario_promedio_250_semanas(self, periodos: List[PeriodoLaboral], fecha_emision: str) -> float:
        """Calcula salario promedio de las últimas 250 semanas"""
        if not periodos or not fecha_emision:
            return 0.0
        
        try:
            fecha_fin = datetime.strptime(fecha_emision, '%Y-%m-%d')
            fecha_inicio = fecha_fin - timedelta(days=1750)  # 250 semanas = 1750 días
            
            salarios_dias = []
            fecha_actual = fecha_inicio
            
            while fecha_actual <= fecha_fin:
                salarios_fecha = []
                
                # Buscar empleos activos en esta fecha
                for periodo in periodos:
                    if not periodo.fecha_alta:
                        continue
                    
                    inicio_periodo = datetime.strptime(periodo.fecha_alta, '%Y-%m-%d')
                    
                    if periodo.fecha_baja:
                        fin_periodo = datetime.strptime(periodo.fecha_baja, '%Y-%m-%d')
                    else:
                        fin_periodo = fecha_fin  # Empleo vigente
                    
                    if inicio_periodo <= fecha_actual <= fin_periodo:
                        salarios_fecha.append(periodo.salario_base)
                
                # En caso de traslape, tomar el menor salario
                if salarios_fecha:
                    salarios_dias.append(min(salarios_fecha))
                
                fecha_actual += timedelta(days=1)
            
            return round(sum(salarios_dias) / len(salarios_dias), 2) if salarios_dias else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando salario promedio: {e}")
            return 0.0
    
    def _calcular_pension_ley73(self, semanas: int, salario_promedio: float) -> float:
        """Cálculo pensión Ley 73"""
        if semanas < 500:
            return 0.0
        
        # Cuantía básica (35% del salario promedio)
        cuantia_basica = salario_promedio * 0.35
        
        # Incrementos por semanas adicionales (0.563% por semana después de 500)
        semanas_adicionales = max(0, semanas - 500)
        incremento = semanas_adicionales * (salario_promedio * 0.00563)
        
        pension_diaria = cuantia_basica + incremento
        pension_mensual = pension_diaria * 30.4
        
        # Aplicar límites
        pension_minima = self.salario_minimo_2024 * 30.4
        pension_maxima = self.uma_2024 * 25 * 30.4
        
        return min(max(pension_mensual, pension_minima), pension_maxima)
    
    def _calcular_pension_ley97(self, semanas: int, salario_promedio: float, periodos: List[PeriodoLaboral]) -> float:
        """Cálculo pensión Ley 97 (estimación básica)"""
        if semanas < 1250:
            return self.pension_garantizada_2024
        
        # Estimación del saldo acumulado en AFORE
        saldo_estimado = 0
        for periodo in periodos:
            if periodo.dias_laborados and periodo.salario_base > 0:
                # Contribución total: 11.125% (6.5% trabajador + 4.625% patrón)
                contribucion_total = periodo.salario_base * periodo.dias_laborados * 0.11125
                saldo_estimado += contribucion_total
        
        # Renta vitalicia estimada (simplificada)
        # Factor aproximado para convertir saldo a pensión mensual
        factor_renta = 0.00417  # Aproximadamente 4.17% anual / 12 meses
        pension_mensual = saldo_estimado * factor_renta
        
        return max(pension_mensual, self.pension_garantizada_2024)
    
    def _calcular_costo_modalidad40(self, salario_promedio: float) -> float:
        """Calcula costo mensual de Modalidad 40"""
        # Base de cotización: entre 1 y 25 UMA
        base_cotizacion = min(max(salario_promedio, self.uma_2024), self.uma_2024 * 25)
        
        # Cuota mensual: 11.4% sobre la base de cotización
        costo_mensual = base_cotizacion * 0.114 * 30.4
        
        return round(costo_mensual, 2)
    
    def _calcular_beneficio_modalidad40(self, salario_promedio: float, semanas_actuales: int) -> float:
        """Calcula beneficio estimado de Modalidad 40"""
        # Incremento en pensión por cada año en Modalidad 40
        # Aproximadamente 0.563% por semana adicional
        incremento_semanal = salario_promedio * 0.00563
        incremento_anual = incremento_semanal * 52  # 52 semanas por año
        incremento_mensual = incremento_anual * 30.4  # Convertir a mensual
        
        return round(incremento_mensual, 2)
    
    def _proyectar_afore(self, data: Dict, periodos: List[PeriodoLaboral], fecha_nacimiento: Optional[str]) -> ProyeccionAfore:
        """Proyección del AFORE"""
        
        # Estimación del saldo actual
        saldo_actual = 0
        for periodo in periodos:
            if periodo.dias_laborados and periodo.salario_base > 0:
                contribucion = periodo.salario_base * periodo.dias_laborados * 0.11125
                saldo_actual += contribucion
        
        # Determinar edad y años para retiro
        edad_actual = 30  # Default si no hay fecha de nacimiento
        if fecha_nacimiento:
            try:
                nac_date = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                edad_actual = (datetime.now() - nac_date).days / 365.25
            except:
                pass
        
        edad_retiro = 65
        años_restantes = max(0, edad_retiro - edad_actual)
        
        # Proyección con crecimiento (5% anual real estimado)
        if años_restantes > 0:
            factor_crecimiento = (1.05) ** años_restantes
            saldo_proyectado = saldo_actual * factor_crecimiento
        else:
            saldo_proyectado = saldo_actual
        
        # Pensión mensual estimada (20 años de esperanza de vida)
        pension_mensual = saldo_proyectado / (20 * 12)
        
        # Generar recomendación
        if pension_mensual > self.pension_garantizada_2024 * 2:
            recomendacion = "Excelente proyección AFORE. Continúe cotizando regularmente."
        elif pension_mensual > self.pension_garantizada_2024:
            recomendacion = "Proyección AFORE aceptable. Considere Modalidad 40 para mejorar."
        else:
            recomendacion = "Proyección AFORE baja. Recomendamos Modalidad 40 y ahorro voluntario."
        
        return ProyeccionAfore(
            saldo_estimado_actual=round(saldo_actual, 2),
            pension_mensual_estimada=round(pension_mensual, 2),
            pension_garantizada=round(self.pension_garantizada_2024, 2),
            edad_retiro_estimada=edad_retiro,
            recomendacion=recomendacion
        )

# Instancia del analizador
analyzer = IMSSAnalyzer()

# Cliente para Google Sheets
def get_sheets_client():
    """Obtiene cliente de Google Sheets"""
    if not SHEETS_CREDS_PATH or not os.path.exists(SHEETS_CREDS_PATH):
        raise HTTPException(status_code=500, detail="Credenciales de Google Sheets no configuradas")
    
    try:
        gc = gspread.service_account(filename=SHEETS_CREDS_PATH)
        return gc
    except Exception as e:
        logger.error(f"Error conectando a Google Sheets: {e}")
        raise HTTPException(status_code=500, detail=f"Error conectando a Google Sheets: {e}")

def write_to_sheets(resultado: ResultadoCompleto):
    """Escribe resultado a Google Sheets"""
    try:
        gc = get_sheets_client()
        sheet = gc.open_by_key(GDRIVE_SHEET_ID)
        
        # Obtener o crear pestaña
        try:
            worksheet = sheet.worksheet(GDRIVE_SHEET_TAB)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=GDRIVE_SHEET_TAB, rows="1000", cols="20")
        
        # Verificar si hay headers
        try:
            headers = worksheet.row_values(1)
            if not headers:
                # Crear headers
                headers = [
                    "timestamp", "archivo", "nss", "curp", "nombre", 
                    "semanas_cotizadas", "semanas_imss", "semanas_descontadas",
                    "salario_promedio_250", "conservacion_derechos", "ley_aplicable",
                    "pension_estimada", "modalidad_40_viable", "costo_modalidad_40",
                    "saldo_afore_estimado", "pension_afore_estimada", "recomendacion",
                    "costo_analisis", "errors"
                ]
                worksheet.append_row(headers)
        except:
            pass
        
        # Preparar fila de datos
        pension_estimada = (resultado.analisis_pensionario.pension_estimada_ley73 or 
                           resultado.analisis_pensionario.pension_estimada_ley97 or 0)
        
        row_data = [
            resultado.timestamp,
            resultado.archivo,
            resultado.nss or "",
            resultado.curp or "",
            resultado.nombre or "",
            resultado.semanas_cotizadas or 0,
            resultado.semanas_imss or 0,
            resultado.semanas_descontadas or 0,
            resultado.analisis_pensionario.salario_promedio_250_semanas,
            "Sí" if resultado.analisis_pensionario.conservacion_derechos else "No",
            resultado.analisis_pensionario.ley_aplicable,
            pension_estimada,
            "Sí" if resultado.analisis_pensionario.modalidad_40_viable else "No",
            resultado.analisis_pensionario.costo_modalidad_40_mensual or 0,
            resultado.proyeccion_afore.saldo_estimado_actual,
            resultado.proyeccion_afore.pension_mensual_estimada,
            resultado.proyeccion_afore.recomendacion,
            resultado.costo_analisis,
            "; ".join(resultado.errors) if resultado.errors else ""
        ]
        
        # Agregar fila
        worksheet.append_row(row_data)
        logger.info(f"Datos escritos en Sheets para NSS: {resultado.nss}")
        
    except Exception as e:
        logger.error(f"Error escribiendo a Sheets: {e}")
        raise

# Endpoints de la API

@app.get("/health")
async def health_check():
    """Health check del backend"""
    return {
        "status": "healthy",
        "service": "IMSS Analysis Backend",
        "version": "2.0.0",
        "parser_url": PARSER_URL,
        "sheets_configured": bool(SHEETS_CREDS_PATH and GDRIVE_SHEET_ID),
        "sheet_id": GDRIVE_SHEET_ID[:10] + "..." if GDRIVE_SHEET_ID else "No configurado",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload-pdf", response_model=ResultadoCompleto)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fecha_nacimiento: Optional[str] = None
):
    """
    Endpoint principal: parsea PDF + análisis completo + escritura a Sheets
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    try:
        # Enviar PDF al parser
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (file.filename, await file.read(), "application/pdf")}
            response = await client.post(PARSER_URL, files=files)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error en parser: {response.text}")
            
            parsed_data = response.json()
        
        # Realizar análisis completo
        resultado = analyzer.analizar_constancia(parsed_data, fecha_nacimiento)
        
        # Escribir a Sheets en background
        background_tasks.add_task(write_to_sheets, resultado)
        
        logger.info(f"Análisis completo realizado para: {resultado.nombre} (NSS: {resultado.nss})")
        return resultado
        
    except httpx.RequestError as e:
        logger.error(f"Error conectando al parser: {e}")
        raise HTTPException(status_code=500, detail="Error conectando al servicio de parsing")
    except Exception as e:
        logger.error(f"Error en upload-pdf: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

@app.post("/analyze-only")
async def analyze_only(parsed_data: Dict, fecha_nacimiento: Optional[str] = None):
    """
    Endpoint para análisis sin parsing (si ya tienes datos parseados)
    """
    try:
        resultado = analyzer.analizar_constancia(parsed_data, fecha_nacimiento)
        return resultado
    except Exception as e:
        logger.error(f"Error en analyze-only: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.post("/sheets-ping")
async def sheets_ping():
    """Test de conexión a Google Sheets"""
    try:
        gc = get_sheets_client()
        sheet = gc.open_by_key(GDRIVE_SHEET_ID)
        
        # Crear pestaña si no existe
        try:
            worksheet = sheet.worksheet(GDRIVE_SHEET_TAB)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=GDRIVE_SHEET_TAB, rows="100", cols="20")
        
        # Escribir fila de prueba
        test_row = [
            datetime.now().isoformat(),
            "PING_TEST.pdf",
            "12345678901",
            "PING123456HTESTPNG01",
            "Usuario de Prueba",
            1000,
            1000,
            0,
            500.0,
            "Sí",
            "97",
            8000.0,
            "Sí",
            2500.0,
            150000.0,
            7500.0,
            "Prueba de conexión exitosa",
            20.0,
            ""
        ]
        
        worksheet.append_row(test_row)
        
        return {
            "ok": True,
            "message": "Conexión a Google Sheets exitosa",
            "sheet_id": GDRIVE_SHEET_ID,
            "tab": GDRIVE_SHEET_TAB,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en sheets-ping: {e}")
        raise HTTPException(status_code=500, detail=f"Error conectando a Sheets: {str(e)}")

@app.get("/parse-debug/{filename}")
async def parse_debug_file(filename: str):
    """
    Debug: envía archivo al parser en modo debug
    """
    # Este endpoint asume que tienes el archivo localmente para debug
    # En producción, usarías el endpoint normal upload-pdf
    return {"message": "Use /upload-pdf para debug en tiempo real"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
