"""
Evaluador final de calidad que consolida todos los resultados
y proporciona una evaluación integral del procesamiento
"""

from typing import Dict, Any, List

class FinalQuality:
    
    def __init__(self):
        self.pesos_evaluacion = {
            'calidad_extraccion': 0.3,
            'precision_calculo_250': 0.25,
            'precision_conservacion': 0.25,
            'consistencia_cruzada': 0.2
        }
    
    def evaluate_final_quality(self, quality_initial: Dict[str, Any],
                              calculo_250: Dict[str, Any],
                              conservacion: Dict[str, Any],
                              validacion_cruzada: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa la calidad final de todo el procesamiento
        
        Returns:
            Dict con evaluación integral y score final
        """
        # Evaluar cada componente
        eval_extraccion = self._evaluar_calidad_extraccion(quality_initial)
        eval_250 = self._evaluar_calculo_250(calculo_250)
        eval_conservacion = self._evaluar_conservacion_derechos(conservacion)
        eval_cruzada = self._evaluar_validacion_cruzada(validacion_cruzada)
        
        # Calcular score final ponderado
        score_final = (
            eval_extraccion['score'] * self.pesos_evaluacion['calidad_extraccion'] +
            eval_250['score'] * self.pesos_evaluacion['precision_calculo_250'] +
            eval_conservacion['score'] * self.pesos_evaluacion['precision_conservacion'] +
            eval_cruzada['score'] * self.pesos_evaluacion['consistencia_cruzada']
        )
        
        # Determinar nivel de calidad final
        nivel_calidad = self._determinar_nivel_calidad(score_final)
        
        # Compilar alertas y errores
        alertas_totales = []
        errores_totales = []
        
        for evaluacion in [eval_extraccion, eval_250, eval_conservacion, eval_cruzada]:
            alertas_totales.extend(evaluacion.get('alertas', []))
            errores_totales.extend(evaluacion.get('errores', []))
        
        # Generar recomendaciones finales
        recomendaciones = self._generar_recomendaciones_finales(
            score_final, nivel_calidad, errores_totales, alertas_totales
        )
        
        return {
            "score_final": round(score_final, 2),
            "nivel_calidad": nivel_calidad,
            "procesamiento_exitoso": len(errores_totales) == 0,
            "confiabilidad": self._determinar_confiabilidad(score_final, errores_totales),
            "evaluaciones_componentes": {
                "extraccion": eval_extraccion,
                "calculo_250_semanas": eval_250,
                "conservacion_derechos": eval_conservacion,
                "validacion_cruzada": eval_cruzada
            },
            "resumen_alertas": {
                "total_errores": len(errores_totales),
                "total_alertas": len(alertas_totales),
                "errores_criticos": errores_totales,
                "alertas_revision": alertas_totales
            },
            "recomendaciones_finales": recomendaciones,
            "pesos_utilizados": self.pesos_evaluacion
        }
    
    def _evaluar_calidad_extraccion(self, quality_initial: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la calidad de la extracción inicial"""
        calidad = quality_initial.get('calidad_extraccion', 'BAJA')
        confianza = quality_initial.get('confianza', 'BAJO')
        diferencia = abs(quality_initial.get('diferencia', 0))
        
        # Asignar score basado en calidad
        if calidad == 'ALTA':
            score = 95
        elif calidad == 'BUENA':
            score = 85
        else:  # BAJA
            score = 50
        
        # Ajustar por diferencia
        if diferencia > 20:
            score -= 10
        elif diferencia > 50:
            score -= 25
        
        alertas = []
        errores = []
        
        if calidad == 'BAJA':
            errores.append("Calidad de extracción insuficiente - faltan períodos laborales")
        elif diferencia > 20:
            alertas.append(f"Diferencia significativa en semanas: {diferencia}")
        
        return {
            "score": max(score, 0),
            "calidad_detectada": calidad,
            "alertas": alertas,
            "errores": errores,
            "detalles": quality_initial
        }
    
    def _evaluar_calculo_250(self, calculo_250: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la calidad del cálculo de 250 semanas"""
        if calculo_250.get('error'):
            return {
                "score": 0,
                "aplicable": False,
                "alertas": [],
                "errores": [calculo_250.get('error', 'Error no especificado')],
                "razon": "Cálculo no aplicable o falló"
            }
        
        if not calculo_250.get('exito', False):
            return {
                "score": 30,
                "aplicable": True,
                "alertas": [],
                "errores": ["Cálculo de 250 semanas no exitoso"],
                "razon": "Falló el cálculo"
            }
        
        score = 90  # Base alta para cálculos exitosos
        alertas = []
        errores = []
        
        # Verificar completitud del período
        periodo = calculo_250.get('periodo_calculo', {})
        dias_calculados = periodo.get('dias_calculados', 0)
        dias_esperados = periodo.get('dias_esperados', 1750)
        
        if dias_calculados < dias_esperados * 0.8:  # Menos del 80%
            score -= 20
            alertas.append(f"Período incompleto: {dias_calculados}/{dias_esperados} días")
        
        # Verificar aplicación de topes
        topes = calculo_250.get('topes_aplicados', {})
        if topes:
            alertas.append(f"Topes salariales aplicados en {len(topes)} años")
        
        # Verificar salario promedio razonable
        salario_promedio = calculo_250.get('salario_promedio_diario', 0)
        if salario_promedio == 0:
            errores.append("Salario promedio calculado es cero")
            score = 20
        elif salario_promedio < 50:  # Muy bajo
            alertas.append("Salario promedio muy bajo - verificar datos")
            score -= 10
        
        return {
            "score": max(score, 0),
            "aplicable": True,
            "alertas": alertas,
            "errores": errores,
            "salario_promedio_calculado": salario_promedio
        }
    
    def _evaluar_conservacion_derechos(self, conservacion: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la calidad del cálculo de conservación de derechos"""
        if not conservacion.get('exito', False):
            return {
                "score": 30,
                "alertas": [],
                "errores": ["Cálculo de conservación de derechos falló"],
                "estado_derechos": "INDETERMINADO"
            }
        
        score = 85  # Base buena
        alertas = []
        errores = []
        
        # Verificar estado de derechos
        estado_derechos = conservacion.get('estado_derechos', {})
        estado = estado_derechos.get('estado', 'INDETERMINADO')
        
        if estado == 'ERROR':
            errores.append("Error en cálculo de fechas de conservación")
            score = 40
        elif estado == 'INDETERMINADO':
            alertas.append("Estado de derechos indeterminado")
            score -= 15
        
        # Verificar disposición de recursos
        semanas_base = conservacion.get('semanas_base', {})
        hay_disposicion = semanas_base.get('hay_disposicion_recursos', False)
        semanas_descontadas = semanas_base.get('semanas_descontadas', 0)
        
        if hay_disposicion and semanas_descontadas > 0:
            alertas.append(f"Disposición de recursos detectada: {semanas_descontadas} semanas")
        
        # Verificar conservación calculada
        calculo_conservacion = conservacion.get('calculo_conservacion', {})
        dias_conservacion = calculo_conservacion.get('dias_conservacion', 0)
        
        if dias_conservacion == 0:
            errores.append("Días de conservación calculados en cero")
            score = 25
        
        return {
            "score": max(score, 0),
            "alertas": alertas,
            "errores": errores,
            "estado_derechos": estado,
            "dias_conservacion": dias_conservacion
        }
    
    def _evaluar_validacion_cruzada(self, validacion_cruzada: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la calidad de la validación cruzada"""
        if not validacion_cruzada.get('validacion_exitosa', False):
            return {
                "score": 60,
                "alertas": validacion_cruzada.get('alertas', []),
                "errores": validacion_cruzada.get('errores', []),
                "score_consistencia": validacion_cruzada.get('score_consistencia', 0)
            }
        
        score_consistencia = validacion_cruzada.get('score_consistencia', 0)
        
        return {
            "score": score_consistencia,
            "alertas": validacion_cruzada.get('alertas', []),
            "errores": validacion_cruzada.get('errores', []),
            "score_consistencia": score_consistencia
        }
    
    def _determinar_nivel_calidad(self, score_final: float) -> str:
        """Determina el nivel de calidad basado en el score final"""
        if score_final >= 90:
            return "EXCELENTE"
        elif score_final >= 80:
            return "BUENA"
        elif score_final >= 70:
            return "ACEPTABLE"
        elif score_final >= 60:
            return "REGULAR"
        else:
            return "DEFICIENTE"
    
    def _determinar_confiabilidad(self, score_final: float, errores: List[str]) -> str:
        """Determina el nivel de confiabilidad del procesamiento"""
        if len(errores) > 0:
            return "BAJA"
        elif score_final >= 85:
            return "ALTA"
        elif score_final >= 70:
            return "MEDIA"
        else:
            return "BAJA"
    
    def _generar_recomendaciones_finales(self, score_final: float, nivel_calidad: str,
                                        errores: List[str], alertas: List[str]) -> List[str]:
        """Genera recomendaciones finales basadas en la evaluación"""
        recomendaciones = []
        
        if errores:
            recomendaciones.append("ACCIÓN REQUERIDA: Corregir errores críticos antes de usar resultados")
            for error in errores[:3]:  # Máximo 3 errores más críticos
                recomendaciones.append(f"- {error}")
        
        if alertas:
            recomendaciones.append("REVISAR: Verificar elementos marcados como alertas")
        
        if score_final >= 85:
            recomendaciones.append("✓ Procesamiento confiable - Resultados listos para uso")
        elif score_final >= 70:
            recomendaciones.append("⚠ Calidad aceptable - Revisar alertas antes de usar")
        else:
            recomendaciones.append("⚠ Calidad insuficiente - Se recomienda revisión manual")
        
        return recomendaciones


