"""
Módulo de corrección post-extracción para cálculos de semanas IMSS.
Aplica correcciones a resultados ya extraídos por el parser principal.

Autor: Sistema de análisis IMSS
Versión: 1.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json

class CorreccionSemanasIMSS:
    """
    Módulo de corrección post-extracción para cálculos de semanas IMSS.
    Aplica correcciones a resultados ya extraídos por el parser principal.
    """
    
    def __init__(self, modo_debug: bool = False):
        self.modo_debug = modo_debug
        self.correcciones_aplicadas = []
    
    def aplicar_correcciones_completas(self, resultado_parser: Dict) -> Dict:
        """
        Aplica TODAS las correcciones identificadas:
        1. Elimina redondeo hacia arriba
        2. Usa fecha_emision para períodos vigentes (ya aplicado en parser)
        3. Maneja empalmes/solapamientos
        
        Args:
            resultado_parser: Resultado completo del parser original
            
        Returns:
            Dict con correcciones aplicadas y métricas de comparación
        """
        # Hacer copia profunda para no modificar original
        resultado_corregido = json.loads(json.dumps(resultado_parser))
        
        # Extraer datos necesarios
        periodos = resultado_corregido['historial_laboral']['periodos']
        fecha_emision = resultado_corregido['datos_basicos']['fecha_emision']
        semanas_imss_oficial = resultado_corregido['datos_basicos']['semanas_imss']
        
        if self.modo_debug:
            print(f"[CORRECCIÓN] Iniciando corrección de {len(periodos)} períodos")
            print(f"[CORRECCIÓN] Usando fecha_emision: {fecha_emision}")
        
        # CORRECCIÓN 1: Recalcular semanas individuales sin redondeo
        periodos_sin_redondeo = self._eliminar_redondeo_semanas(periodos, fecha_emision)
        
        # CORRECCIÓN 2: Calcular semanas sin empalmes (método principal)
        semanas_sin_empalmes = self._calcular_semanas_sin_empalmes(periodos_sin_redondeo, fecha_emision)
        
        # CORRECCIÓN 3: Identificar y reportar empalmes encontrados
        empalmes_detectados = self._detectar_empalmes(periodos_sin_redondeo)
        
        # Actualizar resultado con períodos corregidos
        resultado_corregido['historial_laboral']['periodos'] = periodos_sin_redondeo
        
        # Agregar sección de métricas de corrección
        resultado_corregido['metricas_correccion'] = {
            'semanas_parser_original': resultado_parser['debug']['semanas_calculadas'],
            'semanas_sin_redondeo': sum(p['semanas_corregidas'] for p in periodos_sin_redondeo),
            'semanas_sin_empalmes': semanas_sin_empalmes,
            'semanas_imss_oficial': semanas_imss_oficial,
            'precision_original': abs(resultado_parser['debug']['semanas_calculadas'] - semanas_imss_oficial),
            'precision_final': abs(semanas_sin_empalmes - semanas_imss_oficial),
            'mejora_absoluta': abs(resultado_parser['debug']['semanas_calculadas'] - semanas_imss_oficial) - abs(semanas_sin_empalmes - semanas_imss_oficial),
            'mejora_porcentual': round(((abs(resultado_parser['debug']['semanas_calculadas'] - semanas_imss_oficial) - abs(semanas_sin_empalmes - semanas_imss_oficial)) / abs(resultado_parser['debug']['semanas_calculadas'] - semanas_imss_oficial)) * 100, 1) if resultado_parser['debug']['semanas_calculadas'] != semanas_imss_oficial else 0,
            'empalmes_detectados': len(empalmes_detectados),
            'total_dias_empalme': sum(emp['dias_solapamiento'] for emp in empalmes_detectados),
            'correcciones_aplicadas': self.correcciones_aplicadas.copy()
        }
        
        if self.modo_debug:
            resultado_corregido['debug_correccion'] = {
                'empalmes_detalle': empalmes_detectados,
                'cambios_por_periodo': self._generar_reporte_cambios(
                    resultado_parser['historial_laboral']['periodos'], 
                    periodos_sin_redondeo
                )
            }
            
            # Mostrar resumen en consola
            m = resultado_corregido['metricas_correccion']
            print(f"[CORRECCIÓN] Semanas original: {m['semanas_parser_original']}")
            print(f"[CORRECCIÓN] Semanas sin empalmes: {m['semanas_sin_empalmes']}")
            print(f"[CORRECCIÓN] Mejora: {m['mejora_absoluta']} semanas ({m['mejora_porcentual']}%)")
        
        return resultado_corregido
    
    def _eliminar_redondeo_semanas(self, periodos: List[Dict], fecha_emision: str) -> List[Dict]:
        """Recalcula semanas individuales eliminando redondeo hacia arriba"""
        periodos_corregidos = []
        self.correcciones_aplicadas.append("eliminacion_redondeo_hacia_arriba")
        
        for periodo in periodos:
            periodo_corregido = periodo.copy()
            
            # Calcular semanas sin redondeo
            semanas_sin_redondeo = self._calcular_semanas_sin_redondeo(
                periodo['fecha_inicio'],
                periodo['fecha_fin'],
                fecha_emision
            )
            
            # Mantener valores originales para comparación
            periodo_corregido['semanas_originales'] = periodo['semanas_cotizadas']
            periodo_corregido['semanas_corregidas'] = semanas_sin_redondeo
            periodo_corregido['diferencia_redondeo'] = periodo['semanas_cotizadas'] - semanas_sin_redondeo
            
            # Actualizar valor principal
            periodo_corregido['semanas_cotizadas'] = semanas_sin_redondeo
            
            periodos_corregidos.append(periodo_corregido)
        
        return periodos_corregidos
    
    def _calcular_semanas_sin_redondeo(self, fecha_inicio: str, fecha_fin: str, fecha_emision: str) -> int:
        """Calcula semanas usando solo división entera (sin redondeo hacia arriba)"""
        try:
            inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
            
            if fecha_fin == "Vigente":
                try:
                    fin = datetime.strptime(fecha_emision, '%Y-%m-%d')
                except:
                    fin = datetime.now()
            else:
                fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
            
            diferencia = fin - inicio
            # CORRECCIÓN CLAVE: Solo división entera, sin redondeo
            semanas = diferencia.days // 7
            
            return max(0, semanas)
        except Exception as e:
            if self.modo_debug:
                print(f"[ERROR] Error calculando semanas sin redondeo: {e}")
            return 0
    
    def _calcular_semanas_sin_empalmes(self, periodos: List[Dict], fecha_emision: str) -> int:
        """Calcula semanas totales eliminando completamente los empalmes"""
        self.correcciones_aplicadas.append("eliminacion_empalmes_solapamientos")
        
        dias_ocupados = set()
        
        for periodo in periodos:
            try:
                inicio = datetime.strptime(periodo['fecha_inicio'], '%d/%m/%Y')
                
                if periodo['fecha_fin'] == 'Vigente':
                    try:
                        fin = datetime.strptime(fecha_emision, '%Y-%m-%d')
                    except:
                        fin = datetime.now()
                else:
                    fin = datetime.strptime(periodo['fecha_fin'], '%d/%m/%Y')
                
                # Agregar todos los días únicos del período
                dia_actual = inicio
                while dia_actual <= fin:
                    dias_ocupados.add(dia_actual.date())
                    dia_actual += timedelta(days=1)
                    
            except Exception as e:
                if self.modo_debug:
                    print(f"[ERROR] Error procesando período {periodo.get('patron', 'N/A')}: {e}")
                continue
        
        dias_unicos = len(dias_ocupados)
        semanas_sin_empalmes = dias_unicos // 7  # Solo semanas completas
        
        if self.modo_debug:
            print(f"[CORRECCIÓN] Días únicos trabajados: {dias_unicos}")
            print(f"[CORRECCIÓN] Semanas sin empalmes: {semanas_sin_empalmes}")
        
        return semanas_sin_empalmes
    
    def _detectar_empalmes(self, periodos: List[Dict]) -> List[Dict]:
        """Detecta y cuantifica empalmes entre períodos"""
        empalmes = []
        
        # Ordenar períodos por fecha de inicio
        periodos_ordenados = sorted(periodos, key=lambda x: datetime.strptime(x['fecha_inicio'], '%d/%m/%Y'))
        
        for i in range(len(periodos_ordenados)):
            for j in range(i + 1, len(periodos_ordenados)):
                periodo1 = periodos_ordenados[i]
                periodo2 = periodos_ordenados[j]
                
                empalme = self._calcular_empalme_entre_periodos(periodo1, periodo2)
                if empalme:
                    empalmes.append(empalme)
        
        return empalmes
    
    def _calcular_empalme_entre_periodos(self, periodo1: Dict, periodo2: Dict) -> Dict:
        """Calcula el empalme específico entre dos períodos"""
        try:
            inicio1 = datetime.strptime(periodo1['fecha_inicio'], '%d/%m/%Y')
            inicio2 = datetime.strptime(periodo2['fecha_inicio'], '%d/%m/%Y')
            
            # Determinar fin de cada período
            if periodo1['fecha_fin'] == 'Vigente':
                fin1 = datetime.now()  # Aproximación
            else:
                fin1 = datetime.strptime(periodo1['fecha_fin'], '%d/%m/%Y')
                
            if periodo2['fecha_fin'] == 'Vigente':
                fin2 = datetime.now()
            else:
                fin2 = datetime.strptime(periodo2['fecha_fin'], '%d/%m/%Y')
            
            # Calcular solapamiento
            inicio_solapamiento = max(inicio1, inicio2)
            fin_solapamiento = min(fin1, fin2)
            
            if inicio_solapamiento <= fin_solapamiento:
                dias_solapamiento = (fin_solapamiento - inicio_solapamiento).days + 1
                semanas_solapamiento = dias_solapamiento // 7
                
                return {
                    'patron1': periodo1['patron'][:30],
                    'patron2': periodo2['patron'][:30],
                    'fecha_inicio_empalme': inicio_solapamiento.strftime('%d/%m/%Y'),
                    'fecha_fin_empalme': fin_solapamiento.strftime('%d/%m/%Y'),
                    'dias_solapamiento': dias_solapamiento,
                    'semanas_solapamiento': semanas_solapamiento
                }
        except:
            pass
        
        return None
    
    def _generar_reporte_cambios(self, periodos_orig: List, periodos_corr: List) -> List[Dict]:
        """Genera reporte detallado de cambios por período"""
        cambios = []
        
        for orig, corr in zip(periodos_orig, periodos_corr):
            if orig['semanas_cotizadas'] != corr['semanas_corregidas']:
                cambios.append({
                    'patron': orig['patron'][:40],
                    'fecha_inicio': orig['fecha_inicio'],
                    'fecha_fin': orig['fecha_fin'],
                    'semanas_original': orig['semanas_cotizadas'],
                    'semanas_corregida': corr['semanas_corregidas'],
                    'diferencia': orig['semanas_cotizadas'] - corr['semanas_corregidas'],
                    'tipo_cambio': 'redondeo_eliminado' if orig['fecha_fin'] != 'Vigente' else 'vigente_ajustado'
                })
        
        return cambios

def procesar_con_correcciones(resultado_parser: Dict, modo_debug: bool = False) -> Dict:
    """
    Función de integración simple para aplicar correcciones
    
    Args:
        resultado_parser: Resultado del parser original
        modo_debug: Mostrar información de debug
    
    Returns:
        Resultado con todas las correcciones aplicadas
    """
    corrector = CorreccionSemanasIMSS(modo_debug=modo_debug)
    return corrector.aplicar_correcciones_completas(resultado_parser)


