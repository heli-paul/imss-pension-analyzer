"""
Parser IMSS con conservación de derechos
Cálculo preciso de 250 semanas + análisis de conservación según LSS
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import pdfplumber
import re
from typing import Optional, List, Dict
import tempfile
import os
from datetime import datetime, timedelta
import logging
import sys
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Funciones stub temporales - reemplazar después con archivos reales
def agregar_identificacion_ley(data):
    data["identificacion_ley"] = {
        "ley_aplicable": "indeterminado",
        "fecha_primer_alta": "",
        "años_cotizando_antes_1997": 0,
        "derechos": {"sistema": "", "cumple_requisitos": False}
    }
    return data

def validar_constancia(data):
    return {"score_calidad": 95}

class GoogleSheetsManager:
    """Manejo completo de Google Sheets para constancias IMSS"""
    def __init__(self, credentials_file, spreadsheet_id):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        logger.info("✅ Google Sheets Manager iniciado (modo stub)")

    def crear_hoja_si_no_existe(self, nombre_hoja):
        logger.info(f"✅ Hoja '{nombre_hoja}' creada (stub)")

    def agregar_fila(self, nombre_hoja, datos):
        logger.info(f"✅ Fila agregada a '{nombre_hoja}' (stub)")

    def leer_datos(self, nombre_hoja, rango="A:W"):
        return []

    def obtener_estadisticas_sheet(self, nombre_hoja="Constancias_IMSS"):
        return {"total": 0, "mensaje": "Google Sheets en modo stub"}

class DataStorage:
    def __init__(self):
        self.constancias_procesadas = []

    def agregar_constancia(self, datos):
        """Procesar y almacenar datos de constancia IMSS"""
        conservacion_obj = datos.get('conservacion_derechos')
        validacion = datos.get('validacion', {})
        ley_info = datos.get('identificacion_ley', {})

        if hasattr(conservacion_obj, '__dict__'):
            conservacion = conservacion_obj.__dict__
        else:
            conservacion = conservacion_obj or {}

        registro = {
            'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
            'promedio_250_semanas': datos.get('promedio_250_semanas', 0.0),
            'salario_mensual_estimado': datos.get('resumen', {}).get('salario_mensual_estimado', 0.0),
            'conserva_derechos': conservacion.get('conserva_derechos', False),
            'fecha_conservacion': conservacion.get('fecha_conservacion', ''),
            'semanas_ultimos_5_anos': conservacion.get('semanas_ultimos_5_anos', 0),
            'score_calidad': validacion.get('score_calidad', 0),
            'observaciones': '; '.join(conservacion.get('observaciones', [])),
            'ley_aplicable': ley_info.get('ley_aplicable', 'indeterminado'),
            'fecha_primer_alta': ley_info.get('fecha_primer_alta', ''),
            'anos_cotizando_antes_1997': ley_info.get('años_cotizando_antes_1997', 0),
            'sistema_pension': ley_info.get('derechos', {}).get('sistema', ''),
            'cumple_requisitos_pension': ley_info.get('derechos', {}).get('cumple_requisitos', False)
        }

        self.constancias_procesadas.append(registro)
        if sheets_manager:
            self.enviar_a_sheets(registro)
        return registro

    def enviar_a_sheets(self, registro):
        """Enviar registro a Google Sheets con campos optimizados"""
        try:
            nombre_hoja = "Constancias_IMSS"
            sheets_manager.crear_hoja_si_no_existe(nombre_hoja)

            fila_datos = [
                registro['fecha_procesamiento'], registro['archivo'], registro['nombre_cliente'],
                registro['nss'], registro['curp'], registro['fecha_emision'],
                registro['semanas_cotizadas'], registro['semanas_imss'], registro['semanas_descontadas'],
                registro['semanas_reintegradas'], registro['total_semanas'], round(registro['promedio_250_semanas'], 2),
                round(registro['salario_mensual_estimado'], 2), 'SÍ' if registro['conserva_derechos'] else 'NO',
                registro['fecha_conservacion'], registro['semanas_ultimos_5_anos'], registro['score_calidad'],
                registro['observaciones'], registro['ley_aplicable'], registro['fecha_primer_alta'],
                registro['anos_cotizando_antes_1997'], registro['sistema_pension'],
                'SÍ' if registro['cumple_requisitos_pension'] else 'NO'
            ]

            sheets_manager.agregar_fila(nombre_hoja, fila_datos)
            logger.info(f"✅ Datos enviados a Google Sheets: NSS={registro['nss']}")

        except Exception as e:
            logger.error(f"❌ Error enviando a Google Sheets: {e}")

app = FastAPI(
    title="IMSS Parser API",
    description="Parser con conservación de derechos",
    version="2.3.0"
)

# Configuración de Google Sheets
CREDENTIALS_FILE = "/home/heli_paul/imss-pension-analyzer/src/parser/credentials.json"
SPREADSHEET_ID = "1PGb0makALNm_nLlwl6gdu3ecv9gbJcY7JC9uHHq5mrk"

try:
    sheets_manager = GoogleSheetsManager(CREDENTIALS_FILE, SPREADSHEET_ID)
except Exception as e:
    logger.warning(f"Google Sheets no configurado: {e}")
    sheets_manager = None

data_storage = DataStorage()

class PeriodoLaboral(BaseModel):
    empresa: str
    registro_patronal: str
    entidad_federativa: str
    fecha_alta: str
    fecha_baja: Optional[str]
    salario_base: float
    vigente: bool

class MovimientoSalario(BaseModel):
    tipo_movimiento: str
    fecha: str
    salario_diario: float
    empresa: Optional[str] = ""
    registro_patronal: Optional[str] = ""

class ConservacionDerechos(BaseModel):
    conserva_derechos: bool
    fecha_conservacion: Optional[str] = None
    fecha_ultima_baja: Optional[str] = None
    periodo_conservacion_meses: Optional[int] = None
    semanas_ultimos_5_anos: Optional[int] = None
    cumple_requisitos: bool = False
    observaciones: List[str] = []

class ResultadoParsing(BaseModel):
    archivo: str
    resumen: Optional[Dict] = None
    nss: Optional[str] = None
    curp: Optional[str] = None
    nombre: Optional[str] = None
    fecha_emision: Optional[str] = None
    semanas_cotizadas: Optional[int] = None
    semanas_imss: Optional[int] = None
    semanas_descontadas: Optional[int] = None
    semanas_reintegradas: Optional[int] = None
    total_semanas: Optional[int] = None
    periodos_laborales: List[PeriodoLaboral] = []
    movimientos_salario: List[MovimientoSalario] = []
    promedio_250_semanas: Optional[float] = None
    semanas_para_calculo: Optional[int] = None
    conservacion_derechos: Optional[ConservacionDerechos] = None
    errors: List[str] = []

class IMSSParser:
    def __init__(self):
        self.patterns = {
            'nss': [
                r'NSS:\s*(\d{11})',
                r'NSS\s+(\d{11})',
                r'Número de Seguridad Social:\s*(\d{11})'
            ],
            'curp': [
                r'CURP:\s*([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})',
                r'CURP\s+([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})'
            ],
            'nombre': [
                r'reporte\s*\n.*?\n\s*([A-ZÁÉÍÓÚÑ\s]+[A-ZÁÉÍÓÚÑ])\s*\n',
                r'Estimado\(a\),?\s*\n\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'Asegurado:\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'NOMBRE:\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'([A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,})',
            ],
            'fecha_emision': [
                r'Fecha de emisión.*?(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
                r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
                r'reporte\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
            ]
        }

    def _clean_name(self, name_text):
        if not name_text:
            return None
        cleaned = re.sub(r'\s+', ' ', name_text.strip())
        unwanted_patterns = [
            r'asegurado\s*:?\s*', r'nombre\s*:?\s*', r'del\s+asegurado\s*:?\s*',
            r'\s+dd\s+mm\s+yyyy\s*$', r'\s+dd\s+mm\s+aaaa\s*$',
        ]
        for pattern in unwanted_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _extract_semanas_detalle(self, text, resultado):
        try:
            if not resultado.semanas_cotizadas:
                pattern_total = r'total\s+de\s+semanas\s+cotizadas\s*:?\s*(\d+)'
                match = re.search(pattern_total, text, re.IGNORECASE)
                if match:
                    resultado.semanas_cotizadas = int(match.group(1))

            pattern_detalle = r'Tu\s+detalle\s+de\s+semanas.*?(\d+)\s+(\d+)\s+(\d+)'
            match = re.search(pattern_detalle, text, re.IGNORECASE | re.DOTALL)

            if match:
                resultado.semanas_imss = int(match.group(1))
                resultado.semanas_descontadas = int(match.group(2))
                resultado.semanas_reintegradas = int(match.group(3))
                resultado.total_semanas = resultado.semanas_imss - resultado.semanas_descontadas + resultado.semanas_reintegradas

        except Exception as e:
            logger.error(f"Error extrayendo semanas: {e}")
        return resultado

    def _extract_movimientos_salario(self, pdf, resultado):
        try:
            movimientos = []
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            patron_movimientos = r'(ALTA|BAJA|REINGRESO|MODIFICACION\s+DE\s+SALARIO)\s+(\d{2}/\d{2}/\d{4})\s+\$\s*([\d,]+\.?\d*)'
            matches_movimientos = re.finditer(patron_movimientos, full_text, re.IGNORECASE)

            for match in matches_movimientos:
                tipo = match.group(1).strip()
                fecha = match.group(2).strip()
                salario = float(match.group(3).replace(',', ''))
                movimiento = MovimientoSalario(
                    tipo_movimiento=tipo, fecha=fecha, salario_diario=salario,
                    empresa="", registro_patronal=""
                )
                movimientos.append(movimiento)

            if not movimientos:
                patron = r'Nombre\s+del\s+patrón\s+([^\n]+)\s*\n\s*Registro\s+Patronal\s+([^\n]+)\s*\n.*?Fecha\s+de\s+alta\s+(\d{2}/\d{2}/\d{4})\s+Fecha\s+de\s+baja\s+([^\$]*?)\s*Salario\s+Base.*?\$\s*([\d,]+\.?\d*)'
                matches = re.finditer(patron, full_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)

                for match in matches:
                    empresa = match.group(1).strip()
                    registro = match.group(2).strip()
                    fecha_alta = match.group(3).strip()
                    fecha_baja_raw = match.group(4).strip()
                    salario = float(match.group(5).replace(',', ''))

                    mov_alta = MovimientoSalario(
                        tipo_movimiento='ALTA', fecha=fecha_alta, salario_diario=salario,
                        empresa=empresa, registro_patronal=registro
                    )
                    movimientos.append(mov_alta)

                    fecha_baja_clean = re.sub(r'[^\d/]', '', fecha_baja_raw)
                    if re.match(r'\d{2}/\d{2}/\d{4}', fecha_baja_clean):
                        mov_baja = MovimientoSalario(
                            tipo_movimiento='BAJA', fecha=fecha_baja_clean, salario_diario=salario,
                            empresa=empresa, registro_patronal=registro
                        )
                        movimientos.append(mov_baja)

            movimientos.sort(key=lambda x: datetime.strptime(x.fecha, '%d/%m/%Y'), reverse=True)
            resultado.movimientos_salario = movimientos
            logger.info(f"Extraídos {len(movimientos)} movimientos de salario")

        except Exception as e:
            logger.error(f"Error extrayendo movimientos: {e}")
            resultado.errors.append(f"Error extrayendo movimientos: {e}")
        return resultado

    def _extract_periodos_laborales(self, pdf, resultado):
        try:
            periodos = []
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            patron = r'Nombre\s+del\s+patrón\s+([^\n]+)\s*\n\s*Registro\s+Patronal\s+([^\n]+)\s*\n\s*Entidad\s+federativa\s+([^\n]+)\s*\n\s*Fecha\s+de\s+alta\s+(\d{2}/\d{2}/\d{4})\s+Fecha\s+de\s+baja\s+([^\$]*?)\s*Salario\s+Base.*?\$\s*([\d,]+\.?\d*)'
            matches = re.finditer(patron, full_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)

            for match in matches:
                empresa = match.group(1).strip()
                registro = match.group(2).strip()
                entidad = match.group(3).strip()
                fecha_alta = match.group(4).strip()
                fecha_baja_raw = match.group(5).strip()
                salario = float(match.group(6).replace(',', ''))

                fecha_baja = None
                vigente = False
                fecha_baja_clean = re.sub(r'[^\d/]', '', fecha_baja_raw)
                if re.match(r'\d{2}/\d{2}/\d{4}', fecha_baja_clean):
                    fecha_baja = fecha_baja_clean
                else:
                    vigente = True

                periodo = PeriodoLaboral(
                    empresa=empresa, registro_patronal=registro, entidad_federativa=entidad,
                    fecha_alta=fecha_alta, fecha_baja=fecha_baja, salario_base=salario, vigente=vigente
                )
                periodos.append(periodo)

            periodos.sort(key=lambda x: datetime.strptime(x.fecha_alta, '%d/%m/%Y'), reverse=True)
            resultado.periodos_laborales = periodos

        except Exception as e:
            logger.error(f"Error extrayendo períodos: {e}")
        return resultado

    def _calcular_ultimas_250_semanas_imss(self, resultado):
        try:
            if not resultado.movimientos_salario:
                resultado.resumen = {
                    "total_semanas_cotizadas": resultado.semanas_cotizadas,
                    "mensaje": "No hay movimientos de salario para calcular promedio"
                }
                return resultado

            movimientos_ordenados = sorted(
                resultado.movimientos_salario,
                key=lambda x: datetime.strptime(x.fecha, '%d/%m/%Y'),
                reverse=True
            )

            periodos_trabajo = []
            ultimo_salario = None
            fecha_actual = None

            for i, mov in enumerate(movimientos_ordenados):
                fecha_mov = datetime.strptime(mov.fecha, '%d/%m/%Y')

                if mov.tipo_movimiento == 'BAJA':
                    fecha_actual = fecha_mov
                    ultimo_salario = mov.salario_diario
                elif mov.tipo_movimiento in ['ALTA', 'REINGRESO']:
                    if fecha_actual and ultimo_salario:
                        periodos_trabajo.append({
                            'fecha_inicio': fecha_mov, 'fecha_fin': fecha_actual,
                            'salario': ultimo_salario, 'dias': (fecha_actual - fecha_mov).days
                        })
                    fecha_actual = None
                    ultimo_salario = None
                elif mov.tipo_movimiento == 'MODIFICACION DE SALARIO':
                    if fecha_actual and ultimo_salario:
                        periodos_trabajo.append({
                            'fecha_inicio': fecha_mov, 'fecha_fin': fecha_actual,
                            'salario': ultimo_salario, 'dias': (fecha_actual - fecha_mov).days
                        })
                    fecha_actual = fecha_mov
                    ultimo_salario = mov.salario_diario

            if fecha_actual and ultimo_salario:
                periodos_trabajo.append({
                    'fecha_inicio': datetime(1990, 1, 1), 'fecha_fin': fecha_actual,
                    'salario': ultimo_salario, 'dias': (fecha_actual - datetime(1990, 1, 1)).days
                })

            periodos_trabajo.sort(key=lambda x: x['fecha_fin'], reverse=True)

            dias_objetivo = 250 * 7
            dias_acumulados = 0
            suma_ponderada = 0

            for periodo in periodos_trabajo:
                if dias_acumulados >= dias_objetivo:
                    break

                dias_periodo = periodo['dias']
                if dias_periodo <= 0:
                    continue

                if dias_acumulados + dias_periodo <= dias_objetivo:
                    suma_ponderada += periodo['salario'] * dias_periodo
                    dias_acumulados += dias_periodo
                else:
                    dias_faltantes = dias_objetivo - dias_acumulados
                    suma_ponderada += periodo['salario'] * dias_faltantes
                    dias_acumulados = dias_objetivo

            promedio_250_semanas = suma_ponderada / dias_acumulados if dias_acumulados > 0 else 0

            resultado.promedio_250_semanas = round(promedio_250_semanas, 2)
            resultado.semanas_para_calculo = min(int(dias_acumulados / 7), 250)

            resultado.resumen = {
                "promedio_salario_250_semanas": resultado.promedio_250_semanas,
                "semanas_analizadas": resultado.semanas_para_calculo,
                "total_semanas_cotizadas": resultado.semanas_cotizadas,
                "salario_mensual_estimado": round((resultado.promedio_250_semanas * 30), 2) if resultado.promedio_250_semanas else None,
                "periodos_analizados": len(periodos_trabajo),
                "dias_calculados": dias_acumulados
            }

            logger.info(f"Promedio 250 semanas calculado: ${resultado.promedio_250_semanas}")

        except Exception as e:
            logger.error(f"Error calculando 250 semanas: {e}")
            resultado.promedio_250_semanas = None
            resultado.semanas_para_calculo = None
            resultado.resumen = {
                "total_semanas_cotizadas": resultado.semanas_cotizadas,
                "error": f"No se pudo calcular promedio salarial: {str(e)}"
            }

        return resultado

    def _extract_conservacion_derechos(self, full_text, resultado):
        """Extrae información de conservación de derechos del PDF"""
        try:
            conservacion = ConservacionDerechos(
                conserva_derechos=False, cumple_requisitos=False, observaciones=[]
            )

            patron_conservacion = r'CONSERVACION\s+DERECHOS\s*:?\s*(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})'
            match_conservacion = re.search(patron_conservacion, full_text, re.IGNORECASE)

            if match_conservacion:
                dia, mes, año = match_conservacion.groups()
                conservacion.fecha_conservacion = f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
                logger.info(f"Fecha conservación encontrada: {conservacion.fecha_conservacion}")

            patron_ultima_baja = r'FEC\.\s*BAJA\s*ULT\.\s*PERIODO\s*:?\s*(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})'
            match_ultima_baja = re.search(patron_ultima_baja, full_text, re.IGNORECASE)

            if match_ultima_baja:
                dia, mes, año = match_ultima_baja.groups()
                conservacion.fecha_ultima_baja = f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
                logger.info(f"Fecha última baja encontrada: {conservacion.fecha_ultima_baja}")

            patron_con_derecho = r'CON\s+DERECHO\s+(SI|NO)'
            match_derecho = re.search(patron_con_derecho, full_text, re.IGNORECASE)

            if match_derecho:
                conservacion.conserva_derechos = match_derecho.group(1).upper() == 'SI'
                logger.info(f"Indicador derecho encontrado: {match_derecho.group(1)}")

            conservacion = self._calcular_conservacion_derechos(conservacion, resultado)
            resultado.conservacion_derechos = conservacion
            logger.info(f"Conservación de derechos procesada exitosamente")

        except Exception as e:
            logger.error(f"Error extrayendo conservación de derechos: {e}")
            resultado.errors.append(f"Error en conservación de derechos: {e}")
            resultado.conservacion_derechos = ConservacionDerechos(
                conserva_derechos=False, cumple_requisitos=False,
                observaciones=[f"Error procesando conservación: {str(e)}"]
            )

        return resultado

    def _calcular_conservacion_derechos(self, conservacion, resultado):
        """Calcula conservación de derechos usando días exactos cotizados"""
        try:
            logger.info(f"DEBUG - Entrando a calcular conservación")
            logger.info(f"DEBUG - Períodos laborales disponibles: {len(resultado.periodos_laborales)}")

            if not resultado.periodos_laborales:
                conservacion.observaciones.append("Faltan períodos laborales para calcular conservación")
                return conservacion

            fecha_baja = None
            if conservacion.fecha_ultima_baja:
                fecha_baja = datetime.strptime(conservacion.fecha_ultima_baja, "%Y-%m-%d")
                logger.info(f"DEBUG - Usando fecha última baja del texto: {conservacion.fecha_ultima_baja}")
            else:
                periodos_con_baja = [p for p in resultado.periodos_laborales if p.fecha_baja]
                if periodos_con_baja:
                    ultimo_periodo = max(periodos_con_baja, key=lambda x: datetime.strptime(x.fecha_baja, '%d/%m/%Y'))
                    fecha_baja = datetime.strptime(ultimo_periodo.fecha_baja, '%d/%m/%Y')
                    conservacion.fecha_ultima_baja = fecha_baja.strftime("%Y-%m-%d")
                    logger.info(f"DEBUG - Calculada fecha última baja desde períodos: {conservacion.fecha_ultima_baja}")
                else:
                    fecha_baja = datetime.now()
                    conservacion.fecha_ultima_baja = fecha_baja.strftime("%Y-%m-%d")
                    logger.info(f"DEBUG - Usando fecha actual como última baja: {conservacion.fecha_ultima_baja}")

            dias_cotizados_totales = 0
            fechas_ocupadas = set()

            for periodo in resultado.periodos_laborales:
                try:
                    fecha_alta = datetime.strptime(periodo.fecha_alta, '%d/%m/%Y')
                    fecha_baja_periodo = datetime.strptime(periodo.fecha_baja, '%d/%m/%Y') if periodo.fecha_baja else fecha_baja

                    fecha_actual = fecha_alta
                    while fecha_actual <= fecha_baja_periodo:
                        if fecha_actual not in fechas_ocupadas:
                            fechas_ocupadas.add(fecha_actual)
                            dias_cotizados_totales += 1
                        fecha_actual += timedelta(days=1)

                except Exception as e:
                    logger.warning(f"Error procesando período laboral: {e}")
                    continue

            dias_conservacion = dias_cotizados_totales // 4
            conservacion.periodo_conservacion_meses = dias_conservacion // 30

            fecha_conservacion = fecha_baja + timedelta(days=dias_conservacion)
            conservacion.fecha_conservacion = fecha_conservacion.strftime("%Y-%m-%d")

            fecha_actual_now = datetime.now()
            conservacion.conserva_derechos = fecha_actual_now <= fecha_conservacion

            fecha_limite_5_anos = fecha_baja - timedelta(days=365*5)
            dias_ultimos_5_anos = 0

            for fecha in fechas_ocupadas:
                if fecha >= fecha_limite_5_anos:
                    dias_ultimos_5_anos += 1

            conservacion.semanas_ultimos_5_anos = dias_ultimos_5_anos // 7
            conservacion.cumple_requisitos = conservacion.semanas_ultimos_5_anos >= 52

            if conservacion.conserva_derechos:
                conservacion.observaciones.append(f"Conserva derechos hasta {fecha_conservacion.strftime('%d/%m/%Y')}")
            else:
                conservacion.observaciones.append(f"Perdió derechos el {fecha_conservacion.strftime('%d/%m/%Y')}")

            if not conservacion.cumple_requisitos:
                conservacion.observaciones.append("No cumple requisito mínimo de 52 semanas en últimos 5 años")

            logger.info(f"DEBUG - Días cotizados totales: {dias_cotizados_totales}")
            logger.info(f"DEBUG - Días de conservación: {dias_conservacion}")
            logger.info(f"DEBUG - Fecha conservación calculada: {fecha_conservacion.strftime('%d/%m/%Y')}")

        except Exception as e:
            logger.error(f"Error calculando conservación de derechos: {e}")
            conservacion.observaciones.append(f"Error en cálculo: {e}")

        return conservacion

    def parse_pdf(self, pdf_path: str, filename: str) -> ResultadoParsing:
        resultado = ResultadoParsing(archivo=filename)

        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"

                logger.info(f"Texto extraído: {len(full_text)} caracteres")

                resultado = self._extract_basic_info(full_text, resultado)
                resultado = self._extract_semanas_detalle(full_text, resultado)
                resultado = self._extract_periodos_laborales(pdf, resultado)
                resultado = self._extract_movimientos_salario(pdf, resultado)
                resultado = self._calcular_ultimas_250_semanas_imss(resultado)
                resultado = self._extract_conservacion_derechos(full_text, resultado)
                resultado = self._validate_and_clean(resultado)

        except Exception as e:
            logger.error(f"Error parseando PDF: {str(e)}")
            resultado.errors.append(f"Error general: {str(e)}")

        return resultado

    def _extract_basic_info(self, text: str, resultado: ResultadoParsing) -> ResultadoParsing:
        # NSS
        for pattern in self.patterns['nss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                resultado.nss = match.group(1)
                break

        # CURP
        for pattern in self.patterns['curp']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                resultado.curp = match.group(1)
                break

        # Nombre
        for pattern in self.patterns['nombre']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                nombre_candidato = match.group(1).strip()
                if len(nombre_candidato.split()) >= 2:
                    resultado.nombre = self._clean_name(nombre_candidato)
                    break

        # Fecha de emisión
        for pattern in self.patterns['fecha_emision']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dia, mes, año = match.groups()
                resultado.fecha_emision = f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
                break

        return resultado

    def _validate_and_clean(self, resultado: ResultadoParsing) -> ResultadoParsing:
        if resultado.nss and len(resultado.nss) != 11:
            resultado.errors.append(f"NSS inválido: {resultado.nss}")

        if resultado.curp and len(resultado.curp) != 18:
            resultado.errors.append(f"CURP inválido: {resultado.curp}")

        if resultado.semanas_cotizadas and resultado.semanas_cotizadas > 3000:
            resultado.errors.append(f"Semanas cotizadas muy altas: {resultado.semanas_cotizadas}")

        logger.info(f"Resultado parsing: NSS={resultado.nss}, CURP={resultado.curp}, "
                   f"Nombre={resultado.nombre}, Semanas={resultado.semanas_cotizadas}")

        return resultado

parser = IMSSParser()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IMSS Parser",
        "version": "2.3.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        resultado = parser.parse_pdf(tmp_path, file.filename)
        logger.info(f"PDF parseado exitosamente: {file.filename}")

        print("DEBUG: Iniciando conversión a diccionario...")

        # Convertir el objeto a diccionario para el validador
        if hasattr(resultado, '__dict__'):
            resultado_dict = resultado.__dict__
        else:
            resultado_dict = resultado

        print("DEBUG: Conversión completada, ejecutando validador...")

        validacion = validar_constancia(resultado_dict)
        print(f"DEBUG: Validación resultado: {validacion}")
        resultado_dict["validacion"] = validacion

        resultado_dict = agregar_identificacion_ley(resultado_dict)
        print("DEBUG: Validación agregada al resultado")

        data_storage.agregar_constancia(resultado_dict)

        return resultado_dict

    except Exception as e:
        logger.error(f"Error parseando PDF {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parseando PDF: {str(e)}")

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
