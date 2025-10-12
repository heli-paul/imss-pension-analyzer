"""
Validador cruzado entre los cálculos de promedio salarial y conservación de derechos
Verifica consistencia entre ambas rutas de cálculo
"""

from typing import Dict, Any, List

class CrossValidator:
    
    def __init__(self):
        self.tolerancia_semanas = 10  # Tolerancia para diferencias en semanas
    
    def validate_cross_calculations(self, calculo_250: Dict[str, Any], 
                                   conservacion: Dict[str, Any], 
                                   datos_basicos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida la consistencia entre los cálculos de ambas rutas
        
        Args:
            calculo_250: Resultado del cálculo de promedio 250 semanas
            conservacion: Resultado del cálculo de conservación de derechos
            datos_basicos: Datos básicos del asegurado
        
        Returns:
            Dict con resultado de validación cruzada
        """
        validaciones = []
        alertas = []
        errores = []
        
        # 1. Validar consistencia de semanas utilizadas
        val_semanas = self._validar_consistencia_semanas(calculo_250, conservacion, datos_basicos)
        validaciones.append(val_semanas)
        
        # 2. Validar coherencia temporal
        val_temporal = self._validar_coherencia_temporal(calculo_250, conservacion, datos_basicos)
        validaciones.append(val_temporal)
        
        # 3. Validar aplicación de ley
        val_ley = self._validar_aplicacion_ley(calculo_250, conservacion, datos_basicos)
        validaciones.append(val_ley)
        
        # 4. Validar disposición de recursos
        val_disposicion = self._validar_disposicion_recursos(calculo_250, conservacion, datos_basicos)
        validaciones.append(val_disposicion)
        
        # 5. Identificar inconsistencias críticas
        for val in validaciones:
            if not val.get('valido', True):
                if val.get('severidad') == 'ERROR':
                    errores.append(val['mensaje'])
                elif val.get('severidad') == 'ALERTA':
                    alertas.append(val['mensaje'])
        
        # Calcular score de consistencia
        score_consistencia = self._calcular_score_consistencia(validaciones)
        
        return {
            "validacion_exitosa": len(errores) == 0,
            "score_consistencia": score_consistencia,
            "validaciones_realizadas": len(validaciones),
            "validaciones_exitosas": len([v for v in validaciones if v.get('valido', True)]),
            "errores": errores,
            "alertas": alertas,
            "detalle_validaciones": validaciones,
            "recomendaciones": self._generar_recomendaciones(validaciones)
        }
    
    def _validar_consistencia_semanas(self, calculo_250: Dict[str, Any], 
                                     conservacion: Dict[str, Any], 
                                     datos_basicos: Dict[str, Any]) -> Dict[str, Any]:
        """Valida que ambos cálculos usen las mismas bases de semanas"""
        
        # Semanas de conservación
        semanas_conservacion = conservacion.get('semanas_base', {}).get('semanas_efectivas', 0)
        
        # Semanas utilizadas en cálculo 250
        if calculo_250.get('error'):
            return {
                "nombre": "consistencia_semanas",
                "valido": True,
                "mensaje": "No aplicable - cálculo 250 semanas no disponible",
                "severidad": "INFO"
            }
        
        semanas_periodo = calculo_250.get('periodo_calculo', {})
        dias_calculados = semanas_periodo.get('dias_calculados', 0)
        semanas_250_utilizadas = dias_calculados // 7
        
        # Comparar con datos básicos
        total_semanas_datos = datos_basicos.get('total_semanas', 0)
        
        if abs(semanas_conservacion - total_semanas_datos) <= self.tolerancia_semanas:
            return {
                "nombre": "consistencia_semanas",
                "valido": True,
                "mensaje": "Semanas consistentes entre cálculos",
                "datos": {
                    "semanas_conservacion": semanas_conservacion,
                    "total_semanas_datos": total_semanas_datos,
                    "diferencia": abs(semanas_conservacion - total_semanas_datos)
                },
                "severidad": "OK"
            }
        else:
            return {
                "nombre": "consistencia_semanas",
                "valido": False,
                "mensaje": f"Inconsistencia en semanas: {semanas_conservacion} vs {total_semanas_datos}",
                "datos": {
                    "semanas_conservacion": semanas_conservacion,
                    "total_semanas_datos": total_semanas_datos,
                    "diferencia": abs(semanas_conservacion - total_semanas_datos)
                },
                "severidad": "ALERTA"
            }
    
    def _validar_coherencia_temporal(self, calculo_250: Dict[str, Any], 
                                   conservacion: Dict[str, Any], 
                                   datos_basicos: Dict[str, Any]) -> Dict[str, Any]:
        """Valida coherencia temporal entre cálculos"""
        
        fecha_emision = datos_basicos.get('fecha_emision')
        
        # Fechas de conservación
        fechas_conservacion = conservacion.get('fechas_conservacion', {})
        fecha_fin_conservacion = fechas_conservacion.get('fecha_fin_conservacion')
        
        # Período de cálculo 250 semanas
        if calculo_250.get('error'):
            return {
                "nombre": "coherencia_temporal",
                "valido": True,
                "mensaje": "No aplicable - cálculo 250 semanas no disponible",
                "severidad": "INFO"
            }
        
        periodo_calculo = calculo_250.get('periodo_calculo', {})
        fecha_fin_calculo = periodo_calculo.get('fecha_fin')
        
        # Verificar coherencia
        if fecha_emision and fecha_fin_calculo and fecha_emision == fecha_fin_calculo:
            return {
                "nombre": "coherencia_temporal",
                "valido": True,
                "mensaje": "Fechas de referencia coherentes",
                "datos": {
                    "fecha_emision": fecha_emision,
                    "fecha_fin_calculo_250": fecha_fin_calculo,
                    "fecha_fin_conservacion": fecha_fin_conservacion
                },
                "severidad": "OK"
            }
        else:
            return {
                "nombre": "coherencia_temporal",
                "valido": False,
                "mensaje": "Inconsistencia en fechas de referencia",
                "datos": {
                    "fecha_emision": fecha_emision,
                    "fecha_fin_calculo_250": fecha_fin_calculo,
                    "fecha_fin_conservacion": fecha_fin_conservacion
                },
                "severidad": "ALERTA"
            }
    
    def _validar_aplicacion_ley(self, calculo_250: Dict[str, Any], 
                               conservacion: Dict[str, Any], 
                               datos_basicos: Dict[str, Any]) -> Dict[str, Any]:
        """Valida que ambos cálculos apliquen la misma ley"""
        
        ley_datos = datos_basicos.get('ley_aplicable', 'No determinada')
        ley_250 = calculo_250.get('ley_aplicable', 'No determinada')
        ley_conservacion = conservacion.get('ley_aplicable', 'No determinada')
        
        if ley_datos == ley_250 == ley_conservacion:
            return {
                "nombre": "aplicacion_ley",
                "valido": True,
                "mensaje": f"Ley aplicada consistentemente: {ley_datos}",
                "datos": {"ley_aplicable": ley_datos},
                "severidad": "OK"
            }
        else:
            return {
                "nombre": "aplicacion_ley",
                "valido": False,
                "mensaje": "Inconsistencia en ley aplicable entre cálculos",
                "datos": {
                    "ley_datos_basicos": ley_datos,
                    "ley_calculo_250": ley_250,
                    "ley_conservacion": ley_conservacion
                },
                "severidad": "ERROR"
            }
    
    def _validar_disposicion_recursos(self, calculo_250: Dict[str, Any], 
                                    conservacion: Dict[str, Any], 
                                    datos_basicos: Dict[str, Any]) -> Dict[str, Any]:
        """Valida el manejo de disposición de recursos"""
        
        semanas_descontadas = datos_basicos.get('semanas_descontadas', 0)
        
        if semanas_descontadas > 0:
            # Debe haber impacto en conservación
            hay_disposicion_conservacion = conservacion.get('semanas_base', {}).get('hay_disposicion_recursos', False)
            
            if hay_disposicion_conservacion:
                return {
                    "nombre": "disposicion_recursos",
                    "valido": True,
                    "mensaje": f"Disposición de recursos ({semanas_descontadas} semanas) aplicada correctamente",
                    "datos": {"semanas_descontadas": semanas_descontadas},
                    "severidad": "OK"
                }
            else:
                return {
                    "nombre": "disposicion_recursos",
                    "valido": False,
                    "mensaje": "Disposición de recursos no reflejada en cálculo de conservación",
                    "datos": {"semanas_descontadas": semanas_descontadas},
                    "severidad": "ERROR"
                }
        else:
            return {
                "nombre": "disposicion_recursos",
                "valido": True,
                "mensaje": "Sin disposición de recursos detectada",
                "datos": {"semanas_descontadas": 0},
                "severidad": "OK"
            }
    
    def _calcular_score_consistencia(self, validaciones: List[Dict[str, Any]]) -> float:
        """Calcula un score de consistencia basado en las validaciones"""
        if not validaciones:
            return 0.0
        
        puntos_totales = len(validaciones) * 100
        puntos_obtenidos = 0
        
        for validacion in validaciones:
            if validacion.get('valido', True):
                if validacion.get('severidad') == 'OK':
                    puntos_obtenidos += 100
                elif validacion.get('severidad') == 'INFO':
                    puntos_obtenidos += 80
            else:
                if validacion.get('severidad') == 'ALERTA':
                    puntos_obtenidos += 60
                elif validacion.get('severidad') == 'ERROR':
                    puntos_obtenidos += 0
        
        return round((puntos_obtenidos / puntos_totales) * 100, 2)
    
    def _generar_recomendaciones(self, validaciones: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones basadas en las validaciones"""
        recomendaciones = []
        
        for validacion in validaciones:
            if not validacion.get('valido', True):
                if validacion.get('severidad') == 'ERROR':
                    recomendaciones.append(f"CRÍTICO: {validacion['mensaje']} - Requiere revisión inmediata")
                elif validacion.get('severidad') == 'ALERTA':
                    recomendaciones.append(f"REVISAR: {validacion['mensaje']} - Verificar datos de entrada")
        
        if not recomendaciones:
            recomendaciones.append("Todos los cálculos son consistentes - Se puede proceder con confianza")
        
        return recomendaciones


