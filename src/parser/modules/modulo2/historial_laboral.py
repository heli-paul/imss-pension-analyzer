import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

class PeriodoLaboral:
    """Clase wrapper para compatibilidad con código existente"""
    def __init__(self, data: Dict[str, Any]):
        self.__dict__.update(data)
        self._data = data

    def to_dict(self) -> Dict[str, Any]:
        return self._data

class HistorialLaboralExtractor:
    def __init__(self):
        # Patrones base más generales
        self.patron_fecha = r'(\d{2}/\d{2}/\d{4})'
        self.patron_salario = r'\$\s*([\d,\.]+)'
        self.patron_registro = r'([A-Z]?\d{9,10})'
        # Configuración de tolerancia para extracción
        self.rango_busqueda_base = 800 # caracteres a buscar después de cada patrón
        self.tolerancia_espacios = True # permitir espacios variables
        self.modo_debug = False

    def normalizar_texto(self, texto: str) -> str:
        """Normaliza el texto para mejorar la extracción"""
        # Eliminar espacios excesivos pero mantener estructura
        texto_normalizado = re.sub(r'[ \t]+', ' ', texto)
        # Normalizar saltos de línea
        texto_normalizado = re.sub(r'\r\n', '\n', texto_normalizado)
        return texto_normalizado.strip()

    def extraer_datos_basicos(self, texto: str) -> Dict[str, Any]:
        """Usar el extractor básico existente con mapeo de nomenclatura"""
        try:
            from modules.basic_extractor import extract_basic_data_from_pdf
        
        # Extraer datos con tu función existente
            datos_raw = extract_basic_data_from_pdf(texto, "PDF_PROCESADO.pdf")
        
            print(f"[DEBUG] Datos raw recibidos: {list(datos_raw.keys())}")
            print(f"[DEBUG] Valores raw: {datos_raw}")
            print(f"[DEBUG] fecha_nacimiento en raw: {datos_raw.get('fecha_nacimiento')}")  # ✅ NUEVO
            print(f"[DEBUG] edad en raw: {datos_raw.get('edad')}")  # ✅ NUEVO
        
        # Mapear nomenclatura a lo que espera tu sistema
            datos_mapeados = {
                'nombre': datos_raw.get('nombre', ''),
                'nss': datos_raw.get('nss', ''),
                'curp': datos_raw.get('curp', ''),
                'fecha_emision': datos_raw.get('fecha_emision', ''),
                'fecha_nacimiento': datos_raw.get('fecha_nacimiento', ''),  # ✅ AGREGADO
                'edad': datos_raw.get('edad', None),  # ✅ AGREGADO

            
                # Mapear campos críticos
                'semanas_cotizadas_imss': (
                    datos_raw.get('semanas_cotizadas_imss') or
                    datos_raw.get('semanas_imss') or
                    datos_raw.get('semanas_cotizadas') or
                    0  # ✅ Cambiar de 553 a 0
                ),
                'semanas_descontadas': datos_raw.get('semanas_descontadas', 0),  # ✅ Cambiar de 241 a 0
                'semanas_reintegradas': datos_raw.get('semanas_reintegradas', 0),
                'total_semanas_cotizadas': (
                    datos_raw.get('total_semanas_cotizadas') or
                    datos_raw.get('total_semanas') or
                    0  # ✅ Cambiar de 312 a 0
                )
            }
        
            print(f"[DEBUG] Datos mapeados finales:")
            print(f"[DEBUG] fecha_nacimiento mapeado: {datos_mapeados.get('fecha_nacimiento')}")  # ✅ NUEVO
            print(f"[DEBUG] edad mapeada: {datos_mapeados.get('edad')}")  # ✅ NUEVO
            print(f"[DEBUG] semanas_cotizadas_imss={datos_mapeados['semanas_cotizadas_imss']}")
            print(f"[DEBUG] semanas_descontadas={datos_mapeados['semanas_descontadas']}")
            print(f"[DEBUG] total_semanas_cotizadas={datos_mapeados['total_semanas_cotizadas']}")
        
            return datos_mapeados
        
        except Exception as e:
            print(f"[ERROR] Error en extracción: {e}")
            import traceback
            traceback.print_exc()  # ✅ NUEVO: ver el error completo
            return {}

    def extraer_bloques_genericos(self, texto: str) -> List[Tuple[int, int, str]]:
        """
        Extrae bloques de texto que contienen información de períodos laborales
        usando múltiples estrategias genéricas
        """
        bloques = []
        texto_normalizado = self.normalizar_texto(texto)
        # Estrategia 1: Buscar "Nombre del patrón" como separador principal
        marcadores_inicio = list(re.finditer(r'Nombre del patrón', texto_normalizado, re.IGNORECASE))
        for i, marcador in enumerate(marcadores_inicio):
            inicio = marcador.start()
            # Determinar fin del bloque
            if i + 1 < len(marcadores_inicio):
                fin = marcadores_inicio[i + 1].start()
            else:
                fin = len(texto_normalizado)
            bloque_texto = texto_normalizado[inicio:fin]
            bloques.append((inicio, fin, bloque_texto))
        # Estrategia 2: Si no encontramos suficientes bloques, buscar por registros patronales
        if len(bloques) < 5: # umbral mínimo esperado
            marcadores_registro = list(re.finditer(r'Registro Patronal\s+([A-Z]?\d{9,10})', texto_normalizado))
            bloques_adicionales = []
            for i, marcador in enumerate(marcadores_registro):
                # Buscar hacia atrás para encontrar el inicio del patrón
                texto_previo = texto_normalizado[max(0, marcador.start()-200):marcador.start()]
                inicio_patron = texto_previo.rfind('Nombre del patrón')
                if inicio_patron == -1:
                    inicio_patron = max(0, marcador.start()-200)
                else:
                    inicio_patron = max(0, marcador.start()-200) + inicio_patron
                # Determinar fin
                if i + 1 < len(marcadores_registro):
                    fin = marcadores_registro[i + 1].start()
                else:
                    fin = len(texto_normalizado)
                bloque_texto = texto_normalizado[inicio_patron:fin]
                bloques_adicionales.append((inicio_patron, fin, bloque_texto))
            # Combinar y deduplicar bloques
            todos_los_bloques = bloques + bloques_adicionales
            bloques = self._deduplicar_bloques(todos_los_bloques)
        return bloques

    def _deduplicar_bloques(self, bloques: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        """Elimina bloques duplicados o superpuestos"""
        if not bloques:
            return []
        # Ordenar por posición de inicio
        bloques_ordenados = sorted(bloques, key=lambda x: x[0])
        bloques_unicos = [bloques_ordenados[0]]
        for bloque_actual in bloques_ordenados[1:]:
            ultimo_bloque = bloques_unicos[-1]
            # Si no se superponen significativamente, agregarlo
            if bloque_actual[0] >= ultimo_bloque[1] - 50: # tolerancia de 50 caracteres
                bloques_unicos.append(bloque_actual)
        return bloques_unicos

    def extraer_info_periodo_adaptativo(self, bloque: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información de período usando múltiples estrategias adaptativas
        """
        bloque_limpio = self.normalizar_texto(bloque)
        # Intentar extraer cada campo con múltiples patrones
        extractores = {
            'patron': self._extraer_nombre_patron,
            'registro_patronal': self._extraer_registro_patronal,
            'entidad_federativa': self._extraer_entidad,
            'fechas': self._extraer_fechas,
            'salario': self._extraer_salario
        }
        datos_periodo = {}
        for campo, extractor in extractores.items():
            try:
                resultado = extractor(bloque_limpio)
                if resultado:
                    if campo == 'fechas':
                        datos_periodo.update(resultado) # fechas devuelve dict con fecha_inicio y fecha_fin
                    else:
                        datos_periodo[campo] = resultado
            except Exception as e:
                if self.modo_debug:
                    print(f"Error extrayendo {campo}: {e}")
                continue
        # Validar que tenemos los datos mínimos necesarios
        campos_requeridos = ['patron', 'registro_patronal', 'fecha_inicio', 'fecha_fin']
        if all(campo in datos_periodo for campo in campos_requeridos):
            # Completar datos faltantes con valores por defecto
            datos_periodo.setdefault('entidad_federativa', 'TLAXCALA')
            datos_periodo.setdefault('salario', 0.0)
            datos_periodo['esta_vigente'] = datos_periodo.get('fecha_fin') == 'Vigente'
            datos_periodo['salario_diario'] = datos_periodo.get('salario', 0.0)
            return datos_periodo
        return None

    def _extraer_nombre_patron(self, texto: str) -> Optional[str]:
        """Extrae nombre del patrón con múltiples estrategias"""
        patrones = [
            r'Nombre del patrón\s+([^\n\r]+?)(?=\s*(?:Registro Patronal|$))',
            r'Nombre del patrón\s*([^R]+?)(?=Registro)',
            r'patrón\s+([A-ZÁÉÍÓÚÑ\s,\.&\-]+)',
        ]
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                nombre = match.group(1).strip()
                # Validar que no sea demasiado corto o largo
                if 5 <= len(nombre) <= 100:
                    return nombre
        return None

    def _extraer_registro_patronal(self, texto: str) -> Optional[str]:
        """Extrae registro patronal"""
        patrones = [
            r'Registro Patronal\s+([A-Z]?\d{9,10})',
            r'Patronal\s+([A-Z]?\d{9,10})',
            r'([A-Z]\d{9})',
            r'(\d{10})'
        ]
        for patron in patrones:
            match = re.search(patron, texto)
            if match:
                return match.group(1).strip()
        return None

    def _extraer_entidad(self, texto: str) -> Optional[str]:
        """Extrae entidad federativa"""
        patrones = [
            r'Entidad federativa\s+([A-ZÁÉÍÓÚÑ\s]+?)(?=\s*(?:Fecha|$))',
            r'federativa\s+([A-ZÁÉÍÓÚÑ\s]+)',
            r'(TLAXCALA|MÉXICO|PUEBLA|VERACRUZ)' # estados comunes como fallback
        ]
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extraer_fechas(self, texto: str) -> Optional[Dict[str, str]]:
        """Extrae fechas de inicio y fin"""
        # Patrones para fechas en diferentes formatos
        patrones_fechas = [
            r'Fecha de alta\s+(\d{2}/\d{2}/\d{4})\s+Fecha de baja\s+((?:\d{2}/\d{2}/\d{4})|Vigente)',
            r'alta\s+(\d{2}/\d{2}/\d{4})\s*.*?baja\s+((?:\d{2}/\d{2}/\d{4})|Vigente)',
            r'(\d{2}/\d{2}/\d{4})\s+.*?(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})\s+.*?Vigente'
        ]
        for patron in patrones_fechas:
            match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
            if match:
                fecha_inicio = match.group(1)
                try:
                    fecha_fin = match.group(2) if len(match.groups()) > 1 else 'Vigente'
                except:
                    fecha_fin = 'Vigente'
                # Validar formato de fecha
                try:
                    datetime.strptime(fecha_inicio, '%d/%m/%Y')
                    if fecha_fin != 'Vigente':
                        datetime.strptime(fecha_fin, '%d/%m/%Y')
                    return {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}
                except:
                    continue
        return None

    def _extraer_salario(self, texto: str) -> Optional[float]:
        """Extrae salario con múltiples estrategias"""
        patrones = [
            r'Salario Base de Cotización[^$]*\$\s*([\d,\.]+)',
            r'Cotización[^$]*\$\s*([\d,\.]+)',
            r'\$\s*([\d,\.]+)'
        ]
        for patron in patrones:
            matches = re.findall(patron, texto)
            for match in matches:
                try:
                    salario = float(match.replace(',', ''))
                    # Validar rango razonable (entre $1 y $10,000 pesos diarios)
                    if 1.0 <= salario <= 10000.0:
                        return salario
                except:
                    continue
        return None

    def extraer_movimientos_generico(self, bloque: str) -> List[Dict[str, Any]]:
        """Extrae movimientos usando patrones genéricos"""
        movimientos = []
        # Buscar patrones de movimientos en el texto
        patron_movimiento = r'(BAJA|REINGRESO|MODIFICACION DE SALARIO|ALTA)\s+(\d{2}/\d{2}/\d{4})\s+\$\s*([\d,\.]+)'
        matches = re.findall(patron_movimiento, bloque, re.IGNORECASE)
        for match in matches:
            try:
                movimientos.append({
                    'tipo': match[0].upper(),
                    'fecha': match[1],
                    'salario_diario': float(match[2].replace(',', ''))
                })
            except:
                continue
        return movimientos

    # ============== MODIFICACIÓN: MÉTODO CON CORRECCIÓN DE PERÍODOS VIGENTES ==============
    def calcular_semanas_periodo(self, fecha_inicio: str, fecha_fin: str, fecha_emision: str = None) -> int:
        """Calcula las semanas cotizadas en un período - CON CORRECCIÓN PARA VIGENTES"""
        try:
            inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
            if fecha_fin == "Vigente":
                # CORRECCIÓN: Usar fecha_emision antes que datetime.now()
                if fecha_emision:
                    try:
                        fin = datetime.strptime(fecha_emision, '%Y-%m-%d')
                    except:
                        fin = datetime.now() # Fallback si formato es incorrecto
                else:
                    fin = datetime.now() # Mantener comportamiento original
            else:
                fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
            diferencia = fin - inicio
            semanas = diferencia.days // 7
            if diferencia.days % 7 > 0:
                semanas += 1
            return max(0, semanas)
        except:
            return 0

    # ============== MODIFICACIÓN: PASAR FECHA_EMISION AL CALCULAR SEMANAS ==============
    def extraer_periodos(self, texto_pdf: str) -> List[PeriodoLaboral]:
        """
        Método principal que usa estrategias genéricas y adaptativas - CON FECHA_EMISION
        """
        # Extraer bloques usando método genérico
        bloques = self.extraer_bloques_genericos(texto_pdf)
        # NUEVO: Obtener fecha_emision para usarla en cálculos de períodos vigentes
        datos_basicos = self.extraer_datos_basicos(texto_pdf)
        fecha_emision = datos_basicos.get('fecha_emision')
        periodos = []
        for inicio, fin, bloque in bloques:
            # Extraer información del período
            info_periodo = self.extraer_info_periodo_adaptativo(bloque)
            if info_periodo:
                # Extraer movimientos
                movimientos = self.extraer_movimientos_generico(bloque)
                # MODIFICADO: Pasar fecha_emision al cálculo
                semanas = self.calcular_semanas_periodo(
                    info_periodo['fecha_inicio'],
                    info_periodo['fecha_fin'],
                    fecha_emision # <- NUEVA LÍNEA
                )
                # Construir período completo
                periodo = {
                    'patron': info_periodo['patron'],
                    'registro_patronal': info_periodo['registro_patronal'],
                    'entidad_federativa': info_periodo['entidad_federativa'],
                    'fecha_inicio': info_periodo['fecha_inicio'],
                    'fecha_fin': info_periodo['fecha_fin'],
                    'salario_diario': info_periodo['salario_diario'],
                    'esta_vigente': info_periodo['esta_vigente'],
                    'semanas_cotizadas': semanas,
                    'total_movimientos': len(movimientos),
                    'cambios_salario': movimientos
                }
                periodos.append(periodo)
        return [PeriodoLaboral(p) for p in periodos]

    def determinar_ley_aplicable(self, fecha_primer_alta: str) -> str:
        """Determina la ley aplicable basada en la fecha del primer alta"""
        try:
            fecha = datetime.strptime(fecha_primer_alta, '%d/%m/%Y')
            return "Ley 73" if fecha.year < 1997 else "Ley 97"
        except:
            return "No determinada"

    def calcular_anos_antes_1997(self, fecha_primer_alta: str, periodos: List[Dict]) -> float:
        """Calcula años cotizados antes de 1997"""
        try:
            fecha_limite = datetime(1997, 7, 1)
            fecha_primera = datetime.strptime(fecha_primer_alta, '%d/%m/%Y')
            if fecha_primera >= fecha_limite:
                return 0.0
            anos = (fecha_limite - fecha_primera).days / 365.25
            return round(anos, 1)
        except:
            return 0.0

    def validar_consistencia(self, periodos: List[Dict], semanas_imss: int) -> Dict[str, Any]:
        """Valida la consistencia de los datos extraídos"""
        semanas_calculadas = sum(p.get('semanas_cotizadas', 0) for p in periodos)
        return {
            'semanas_calculadas': semanas_calculadas
        }

    def debug_extraccion(self, texto_pdf: str) -> Dict[str, Any]:
        """Método para compatibilidad - devuelve información de debug"""
        resultado = self.procesar_constancia(texto_pdf)
        return resultado.get('debug', {})

    def debug_web(self, texto_pdf: str) -> Dict[str, Any]:
        """Debug para ver qué está pasando con el texto"""
        debug_info = {}
        # Buscar palabras clave básicas
        debug_info["nombre_patron_encontrado"] = "Nombre del patrón" in texto_pdf
        debug_info["registro_patronal_encontrado"] = "Registro Patronal" in texto_pdf
        debug_info["vigente_encontrado"] = "Vigente" in texto_pdf
        debug_info["fechas_encontradas"] = len(re.findall(r'\d{2}/\d{2}/\d{4}', texto_pdf))
        # Muestra del texto
        debug_info["primeros_500_caracteres"] = texto_pdf[:500]
        # Líneas que contienen info importante
        lineas_importantes = []
        for i, linea in enumerate(texto_pdf.split('\n')):
            if any(palabra in linea for palabra in ['Nombre del patrón', 'Registro Patronal', 'Vigente']):
                lineas_importantes.append(f"Línea {i}: {linea.strip()}")
        debug_info["lineas_importantes"] = lineas_importantes[:10]
        return debug_info

    def procesar_constancia_con_debug(self, texto_pdf: str) -> Dict[str, Any]:
        """Procesa la constancia e incluye debug detallado"""
        resultado = self.procesar_constancia(texto_pdf)
        # Agregar debug web
        debug_info = self.debug_web(texto_pdf)
        resultado["debug_web"] = debug_info
        # Agregar información adicional de debug
        bloques = self.extraer_bloques_genericos(texto_pdf)
        resultado["debug"]["total_bloques_encontrados"] = len(bloques)
        resultado["debug"]["metodo_extraccion"] = "estandarizado_generico_con_vigente_corregido"
        return resultado

    def procesar_constancia(self, texto_pdf: str) -> Dict[str, Any]:
        """Procesa toda la constancia usando métodos estandarizados - NOMENCLATURA OFICIAL IMSS"""
        # Extraer datos básicos
        datos_basicos = self.extraer_datos_basicos(texto_pdf)
        # Extraer períodos
        periodos_obj = self.extraer_periodos(texto_pdf)
        periodos = [p.to_dict() for p in periodos_obj]
        # Ordenar períodos cronológicamente
        periodos.sort(key=lambda x: datetime.strptime(x['fecha_inicio'], '%d/%m/%Y'), reverse=True)
        # Calcular estadísticas
        total_movimientos = sum(p.get('total_movimientos', 0) for p in periodos)
        registros_patronales_unicos = set(p.get('registro_patronal', '') for p in periodos)
        # Determinar fecha del primer alta
        fecha_primer_alta = None
        if periodos:
            fecha_primer_alta = min(periodos, key=lambda x: datetime.strptime(x['fecha_inicio'], '%d/%m/%Y'))['fecha_inicio']
        # ✅ USAR NOMENCLATURA OFICIAL PARA VALIDACIÓN
        total_semanas_oficial = datos_basicos.get('total_semanas_cotizadas', 0)
        validacion = self.validar_consistencia(periodos, total_semanas_oficial)
        resultado = {
            "exito": True,
            "archivo": "PDF_PROCESADO.pdf",
            "datos_basicos": {
                "fecha_procesamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo": "PDF_PROCESADO.pdf",
                "nombre": datos_basicos.get('nombre', ''),
                "nss": datos_basicos.get('nss', ''),
                "curp": datos_basicos.get('curp', ''),
                "fecha_emision": datos_basicos.get('fecha_emision', ''),
                "fecha_nacimiento": datos_basicos.get('fecha_nacimiento', ''),  # ✅ NUEVO
                "edad": datos_basicos.get('edad', None),                        # ✅ NUEVO
                # ✅ USAR ÚNICAMENTE NOMENCLATURA OFICIAL IMSS
                "semanas_cotizadas_imss": datos_basicos.get('semanas_cotizadas_imss', 0),
                "semanas_descontadas": datos_basicos.get('semanas_descontadas', 0),
                "semanas_reintegradas": datos_basicos.get('semanas_reintegradas', 0),
                "total_semanas_cotizadas": datos_basicos.get('total_semanas_cotizadas', 0),
                "ley_aplicable": self.determinar_ley_aplicable(fecha_primer_alta) if fecha_primer_alta else "No determinada",
                "fecha_primer_alta": fecha_primer_alta,
                "anos_cotizando_antes_1997": self.calcular_anos_antes_1997(fecha_primer_alta, periodos) if fecha_primer_alta else 0.0,
                "errors": []
            },
            "historial_laboral": {
                "total_periodos": len(periodos),
                "periodos": periodos
            },
            "debug": {
                **validacion,
                "total_movimientos_detectados": total_movimientos,
                "registros_patronales_unicos": len(registros_patronales_unicos),
                "registros_encontrados": list(registros_patronales_unicos),
                "correccion_aplicada": "periodos_vigentes_limitados_a_fecha_emision",
                "nomenclatura": "oficial_imss_estandarizada"
            }
        }
        return resultado

# Función principal
def analizar_constancia_imss(texto_pdf: str) -> str:
    """Función principal que analiza una constancia del IMSS y devuelve JSON"""
    analizador = HistorialLaboralExtractor()
    resultado = analizador.procesar_constancia(texto_pdf)
    return json.dumps(resultado, indent=2, ensure_ascii=False)


