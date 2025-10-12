"""
Módulo de post-procesamiento para corrección exacta de semanas IMSS
Versión final para producción

Uso:
    from correccion_semanas_final import aplicar_correccion_exacta
    resultado_corregido = aplicar_correccion_exacta(resultado_parser)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class CorreccionSemanasIMSS:
    """Corrector de semanas con precisión exacta al IMSS oficial"""
    
    def __init__(self, modo_debug: bool = False):
        self.modo_debug = modo_debug
        self.correcciones_aplicadas = []
    
    def corregir_resultado_completo(self, resultado_parser: Dict) -> Dict:
        """
        Aplica todas las correcciones necesarias para precisión exacta
        CORREGIDO: Usa nomenclatura oficial IMSS

        Args:
            resultado_parser: Resultado del HistorialLaboralExtractor

        Returns:
            Resultado con correcciones aplicadas y precisión exacta
        """
        # Copia profunda para no modificar original
        resultado = json.loads(json.dumps(resultado_parser))

        # Extraer datos necesarios - USAR NOMENCLATURA OFICIAL
        periodos = resultado['historial_laboral']['periodos']
        fecha_emision = resultado['datos_basicos']['fecha_emision']
        
        # ✅ USAR TÉRMINOS OFICIALES IMSS
        total_semanas_oficial = resultado['datos_basicos'].get('total_semanas_cotizadas', 0)
        semanas_originales = resultado['debug']['semanas_calculadas']

        if self.modo_debug:
            print(f"[CORRECCIÓN] Procesando {len(periodos)} períodos")
            print(f"[CORRECCIÓN] Semanas originales: {semanas_originales}")
            print(f"[CORRECCIÓN] Objetivo IMSS: {total_semanas_oficial}")

        # Aplicar correcciones
        periodos_corregidos = self._eliminar_redondeo_periodos(periodos, fecha_emision)
        semanas_sin_empalmes = self._calcular_semanas_sin_empalmes(periodos_corregidos, fecha_emision)
        empalmes_detectados = self._detectar_empalmes(periodos_corregidos)

        # Actualizar resultado
        resultado['historial_laboral']['periodos'] = periodos_corregidos

        # ✅ MÉTRICAS DE CORRECCIÓN CON NOMENCLATURA OFICIAL
        resultado['correccion_aplicada'] = {
            'semanas_parser_original': semanas_originales,
            'semanas_sin_redondeo': sum(p['semanas_corregidas'] for p in periodos_corregidos),
            'total_semanas_cotizadas': semanas_sin_empalmes,  # ✅ Término oficial
            'semanas_cotizadas_imss_calculadas': semanas_sin_empalmes,  # ✅ Término oficial
            'total_semanas_cotizadas_oficial': total_semanas_oficial,  # ✅ Del documento IMSS
            'precision_original': abs(semanas_originales - total_semanas_oficial),
            'precision_final': abs(semanas_sin_empalmes - total_semanas_oficial),
            'mejora_semanas': semanas_originales - semanas_sin_empalmes,
            'es_exacto': semanas_sin_empalmes == total_semanas_oficial,
            'empalmes_corregidos': len(empalmes_detectados),
            'dias_empalme_total': sum(e.get('dias_solapamiento', 0) for e in empalmes_detectados),
            'correcciones_aplicadas': self.correcciones_aplicadas.copy()
        }

        # Actualizar debug principal
        resultado['debug']['total_semanas_cotizadas_calculadas'] = semanas_sin_empalmes  # ✅ Término oficial
        resultado['debug']['correccion_post_procesamiento'] = 'aplicada'

        if self.modo_debug:
            print(f"[CORRECCIÓN] Total semanas cotizadas calculadas: {semanas_sin_empalmes}")
            print(f"[CORRECCIÓN] Precisión: {'EXACTA' if semanas_sin_empalmes == total_semanas_oficial else f'±{abs(semanas_sin_empalmes - total_semanas_oficial)}'}")

        # ✅ NUNCA sobrescribir datos oficiales extraídos del PDF
        # Los datos_basicos son SAGRADOS - solo extracción, nunca modificación
        
        # Crear sección separada para análisis calculado
        if 'analisis_calculado' not in resultado:
            resultado['analisis_calculado'] = {}
        
        resultado['analisis_calculado']['semanas_calculadas_sin_empalmes'] = semanas_sin_empalmes
        
        # Validar si coincide con datos oficiales
        total_oficial = resultado['datos_basicos'].get('total_semanas_cotizadas', 0)
        resultado['analisis_calculado']['diferencia_vs_oficial'] = semanas_sin_empalmes - total_oficial
        resultado['analisis_calculado']['coincide_exacto'] = (semanas_sin_empalmes == total_oficial)
        
        if self.modo_debug:
            print(f"[VALIDACIÓN] Oficial IMSS: {total_oficial}")
            print(f"[VALIDACIÓN] Calculado: {semanas_sin_empalmes}")
            print(f"[VALIDACIÓN] Diferencia: {semanas_sin_empalmes - total_oficial}")

        return resultado

    def _eliminar_redondeo_periodos(self, periodos: List[Dict], fecha_emision: str) -> List[Dict]:
        """Recalcula semanas de cada período sin redondeo hacia arriba"""
        self.correcciones_aplicadas.append("eliminacion_redondeo_hacia_arriba")
        
        periodos_corregidos = []
        for periodo in periodos:
            periodo_corregido = periodo.copy()
            
            # Recalcular sin redondeo
            semanas_sin_redondeo = self._calcular_semanas_sin_redondeo(
                periodo['fecha_inicio'],
                periodo['fecha_fin'], 
                fecha_emision
            )
            
            # Mantener original para referencia
            periodo_corregido['semanas_originales'] = periodo['semanas_cotizadas']
            periodo_corregido['semanas_corregidas'] = semanas_sin_redondeo
            periodo_corregido['diferencia_redondeo'] = periodo['semanas_cotizadas'] - semanas_sin_redondeo
            
            # Actualizar valor principal
            periodo_corregido['semanas_cotizadas'] = semanas_sin_redondeo
            
            periodos_corregidos.append(periodo_corregido)
        
        return periodos_corregidos
    
    def _calcular_semanas_sin_redondeo(self, fecha_inicio: str, fecha_fin: str, fecha_emision: str) -> int:
        """Calcula semanas usando solo división entera (método IMSS)"""
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
            # Solo semanas completas (método IMSS)
            semanas = diferencia.days // 7
            return max(0, semanas)
        except:
            return 0
    
    def _calcular_semanas_sin_empalmes(self, periodos: List[Dict], fecha_emision: str) -> int:
        """Calcula semanas totales usando días únicos (método IMSS oficial)"""
        self.correcciones_aplicadas.append("eliminacion_empalmes_dias_unicos")
        
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
                
                # Agregar cada día único
                dia_actual = inicio
                while dia_actual <= fin:
                    dias_ocupados.add(dia_actual.date())
                    dia_actual += timedelta(days=1)
                    
            except:
                continue
        
        dias_unicos = len(dias_ocupados)
        semanas_exactas = dias_unicos // 7
        
        if self.modo_debug:
            print(f"[CORRECCIÓN] Días únicos trabajados: {dias_unicos}")
            print(f"[CORRECCIÓN] Semanas exactas: {semanas_exactas}")
        
        return semanas_exactas
    
    def _detectar_empalmes(self, periodos: List[Dict]) -> List[Dict]:
        """Detecta empalmes para información de debug"""
        empalmes = []
        periodos_ordenados = sorted(periodos, key=lambda x: datetime.strptime(x['fecha_inicio'], '%d/%m/%Y'))
        
        for i in range(len(periodos_ordenados)):
            for j in range(i + 1, len(periodos_ordenados)):
                empalme = self._calcular_empalme_entre_periodos(periodos_ordenados[i], periodos_ordenados[j])
                if empalme:
                    empalmes.append(empalme)
        
        return empalmes
    
    def _calcular_empalme_entre_periodos(self, periodo1: Dict, periodo2: Dict) -> Dict:
        """Calcula solapamiento específico entre dos períodos"""
        try:
            inicio1 = datetime.strptime(periodo1['fecha_inicio'], '%d/%m/%Y')
            inicio2 = datetime.strptime(periodo2['fecha_inicio'], '%d/%m/%Y')
            
            if periodo1['fecha_fin'] == 'Vigente':
                fin1 = datetime.now()
            else:
                fin1 = datetime.strptime(periodo1['fecha_fin'], '%d/%m/%Y')
                
            if periodo2['fecha_fin'] == 'Vigente':
                fin2 = datetime.now()
            else:
                fin2 = datetime.strptime(periodo2['fecha_fin'], '%d/%m/%Y')
            
            inicio_solapamiento = max(inicio1, inicio2)
            fin_solapamiento = min(fin1, fin2)
            
            if inicio_solapamiento <= fin_solapamiento:
                dias_solapamiento = (fin_solapamiento - inicio_solapamiento).days + 1
                return {
                    'patron1': periodo1['patron'][:30],
                    'patron2': periodo2['patron'][:30],
                    'dias_solapamiento': dias_solapamiento,
                    'semanas_solapamiento': dias_solapamiento // 7
                }
        except:
            pass
        return None

def migrar_nomenclatura_oficial(resultado_parser: Dict) -> Dict:
    """
    Migra datos con nomenclatura antigua a términos oficiales IMSS
    Para compatibilidad con parsers antiguos
    """
    resultado_migrado = json.loads(json.dumps(resultado_parser))  # Deep copy
    
    datos_basicos = resultado_migrado.get('datos_basicos', {})
    
    # MIGRAR CAMPOS ANTIGUOS → OFICIALES
    migraciones = {
        # Campo antiguo → Campo oficial IMSS
        'semanas_imss': 'semanas_cotizadas_imss',
        'semanas_cotizadas': 'total_semanas_cotizadas', 
        'total_semanas': 'total_semanas_cotizadas'
    }
    
    for campo_antiguo, campo_oficial in migraciones.items():
        if campo_antiguo in datos_basicos and campo_oficial not in datos_basicos:
            # Migrar valor
            datos_basicos[campo_oficial] = datos_basicos[campo_antiguo]
            # Eliminar campo antiguo
            del datos_basicos[campo_antiguo]
    
    # Asegurar que existan todos los campos oficiales
    campos_oficiales_requeridos = {
        'semanas_cotizadas_imss': datos_basicos.get('total_semanas_cotizadas', 0),
        'semanas_descontadas': 0,
        'semanas_reintegradas': 0,
        'total_semanas_cotizadas': datos_basicos.get('total_semanas_cotizadas', 0)
    }
    
    for campo, valor_default in campos_oficiales_requeridos.items():
        if campo not in datos_basicos:
            datos_basicos[campo] = valor_default
    
    return resultado_migrado

def aplicar_correccion_exacta(resultado_parser: Dict, debug: bool = False) -> Dict:
    """
    Función principal para aplicar corrección exacta de semanas
    ACTUALIZADA: Incluye migración automática a nomenclatura oficial

    Args:
        resultado_parser: Resultado del HistorialLaboralExtractor
        debug: Mostrar información de procesamiento

    Returns:
        Resultado con semanas exactas al IMSS oficial usando nomenclatura estándar
    """
    # PASO 1: Migrar nomenclatura si es necesario
    resultado_migrado = migrar_nomenclatura_oficial(resultado_parser)
    
    # PASO 2: Aplicar corrección
    corrector = CorreccionSemanasIMSS(modo_debug=debug)
    resultado_corregido = corrector.corregir_resultado_completo(resultado_migrado)
    
    if debug:
        print("✅ Nomenclatura migrada a términos oficiales IMSS")
        
    return resultado_corregido

def mostrar_resumen_correccion(resultado_corregido: Dict) -> None:
    """Muestra resumen de la corrección aplicada - VERSIÓN ACTUALIZADA"""
    corr = resultado_corregido['correccion_aplicada']

    print("=" * 60)
    print("RESUMEN DE CORRECCIÓN APLICADA (NOMENCLATURA OFICIAL)")
    print("=" * 60)
    print(f"Semanas parser original: {corr['semanas_parser_original']}")
    print(f"Total semanas cotizadas (calculadas): {corr['total_semanas_cotizadas']}")
    print(f"Total semanas cotizadas (oficial IMSS): {corr['total_semanas_cotizadas_oficial']}")
    print(f"Mejora obtenida: {corr['mejora_semanas']} semanas")
    precision_texto = "EXACTA" if corr['es_exacto'] else f"±{corr['precision_final']} semanas"
    print(f"Precisión: {precision_texto}")
    print(f"Empalmes corregidos: {corr['empalmes_corregidos']}")
    print("=" * 60)

