"""
Calculador de conservación de derechos según las reglas del IMSS
Maneja disposición de recursos y calcula período de conservación
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

class ConservacionDerechos:
    
    def __init__(self):
        self.minimo_conservacion_dias = 364  # 12 meses mínimo
        self.factor_conservacion = 4  # Semanas × 7 ÷ 4
    
    def calcular_conservacion_derechos(self, datos_basicos: Dict[str, Any], 
                                     historial_laboral: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula la conservación de derechos considerando disposición de recursos
        
        Args:
            datos_basicos: Datos básicos del asegurado
            historial_laboral: Historial laboral procesado
        
        Returns:
            Dict con el cálculo de conservación de derechos
        """
        # Obtener datos básicos
        total_semanas = datos_basicos.get('total_semanas', 0)
        semanas_descontadas = datos_basicos.get('semanas_descontadas', 0)
        semanas_reintegradas = datos_basicos.get('semanas_reintegradas', 0)
        fecha_emision = datos_basicos.get('fecha_emision')
        ley_aplicable = datos_basicos.get('ley_aplicable', 'No determinada')
        
        # Determinar semanas efectivas para conservación
        semanas_efectivas = self._calcular_semanas_efectivas(
            total_semanas, semanas_descontadas, semanas_reintegradas
        )
        
        # Calcular período de conservación
        conservacion_resultado = self._calcular_periodo_conservacion(semanas_efectivas)
        
        # Encontrar fecha de última baja
        fecha_ultima_baja = self._encontrar_ultima_baja(historial_laboral)
        
        # Calcular fechas específicas de conservación
        fechas_conservacion = self._calcular_fechas_conservacion(
            fecha_ultima_baja, conservacion_resultado['dias_conservacion']
        )
        
        # Evaluar estado actual de derechos
        estado_derechos = self._evaluar_estado_actual(
            fechas_conservacion, fecha_emision
        )
        
        return {
            "exito": True,
            "ley_aplicable": ley_aplicable,
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "semanas_base": {
                "total_semanas": total_semanas,
                "semanas_descontadas": semanas_descontadas,
                "semanas_reintegradas": semanas_reintegradas,
                "semanas_efectivas": semanas_efectivas,
                "hay_disposicion_recursos": semanas_descontadas > 0
            },
            "calculo_conservacion": conservacion_resultado,
            "fechas_conservacion": fechas_conservacion,
            "estado_derechos": estado_derechos,
            "detalles": {
                "fecha_ultima_baja": fecha_ultima_baja,
                "formula_aplicada": f"({semanas_efectivas} semanas × 7 días) ÷ {self.factor_conservacion} = {conservacion_resultado['dias_conservacion']} días",
                "minimo_legal": f"{self.minimo_conservacion_dias} días (12 meses)"
            }
        }
    
    def _calcular_semanas_efectivas(self, total_semanas: int, 
                                   semanas_descontadas: int, 
                                   semanas_reintegradas: int) -> int:
        """
        Calcula las semanas efectivas para conservación considerando disposición de recursos
        """
        if semanas_descontadas > 0:
            # Si hay disposición de recursos, se reduce el total
            semanas_efectivas = total_semanas - semanas_descontadas + semanas_reintegradas
            return max(0, semanas_efectivas)  # No puede ser negativo
        
        return total_semanas
    
    def _calcular_periodo_conservacion(self, semanas_efectivas: int) -> Dict[str, Any]:
        """
        Calcula el período de conservación aplicando la fórmula del IMSS
        (Semanas × 7 días) ÷ 4 = días de conservación (mínimo 364 días)
        """
        dias_calculados = (semanas_efectivas * 7) // self.factor_conservacion
        dias_conservacion = max(dias_calculados, self.minimo_conservacion_dias)
        
        return {
            "semanas_base": semanas_efectivas,
            "dias_calculados": dias_calculados,
            "dias_conservacion": dias_conservacion,
            "aplico_minimo_legal": dias_calculados < self.minimo_conservacion_dias,
            "años_conservacion": round(dias_conservacion / 365.25, 2),
            "meses_conservacion": round(dias_conservacion / 30.44, 1)
        }
    
    def _encontrar_ultima_baja(self, historial_laboral: Dict[str, Any]) -> Optional[str]:
        """
        Encuentra la fecha de la última baja del historial laboral
        """
        periodos = historial_laboral.get('periodos', [])
        if not periodos:
            return None
        
        # Buscar el período más reciente que haya terminado (no vigente)
        ultima_baja = None
        fecha_mas_reciente = None
        
        for periodo in periodos:
            if not periodo.get('esta_vigente', False) and periodo.get('fecha_fin'):
                try:
                    fecha_fin = datetime.strptime(periodo['fecha_fin'], '%d/%m/%Y')
                    if fecha_mas_reciente is None or fecha_fin > fecha_mas_reciente:
                        fecha_mas_reciente = fecha_fin
                        ultima_baja = periodo['fecha_fin']
                except (ValueError, KeyError):
                    continue
        
        return ultima_baja
    
    def _calcular_fechas_conservacion(self, fecha_ultima_baja: Optional[str], 
                                    dias_conservacion: int) -> Dict[str, Any]:
        """
        Calcula las fechas específicas del período de conservación
        """
        if not fecha_ultima_baja:
            return {
                "fecha_inicio_conservacion": None,
                "fecha_fin_conservacion": None,
                "error": "No se pudo determinar fecha de última baja"
            }
        
        try:
            fecha_baja_dt = datetime.strptime(fecha_ultima_baja, '%d/%m/%Y')
            fecha_inicio_conservacion = fecha_baja_dt + timedelta(days=1)  # Inicia el día siguiente
            fecha_fin_conservacion = fecha_inicio_conservacion + timedelta(days=dias_conservacion - 1)
            
            return {
                "fecha_ultima_baja": fecha_ultima_baja,
                "fecha_inicio_conservacion": fecha_inicio_conservacion.strftime('%Y-%m-%d'),
                "fecha_fin_conservacion": fecha_fin_conservacion.strftime('%Y-%m-%d'),
                "dias_conservacion": dias_conservacion,
                "periodo_conservacion_legible": f"{fecha_inicio_conservacion.strftime('%d/%m/%Y')} al {fecha_fin_conservacion.strftime('%d/%m/%Y')}"
            }
        
        except ValueError:
            return {
                "fecha_inicio_conservacion": None,
                "fecha_fin_conservacion": None,
                "error": f"Fecha de baja inválida: {fecha_ultima_baja}"
            }
    
    def _evaluar_estado_actual(self, fechas_conservacion: Dict[str, Any], 
                              fecha_emision: str) -> Dict[str, Any]:
        """
        Evalúa si los derechos están vigentes, conservados o perdidos
        """
        if fechas_conservacion.get('error') or not fecha_emision:
            return {
                "estado": "INDETERMINADO",
                "razon": "No se pudo evaluar por falta de datos"
            }
        
        try:
            fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%d')
            fecha_fin_conservacion_dt = datetime.strptime(
                fechas_conservacion['fecha_fin_conservacion'], '%Y-%m-%d'
            )
            
            if fecha_emision_dt <= fecha_fin_conservacion_dt:
                dias_restantes = (fecha_fin_conservacion_dt - fecha_emision_dt).days
                return {
                    "estado": "VIGENTE",
                    "derechos_conservados": True,
                    "dias_restantes": dias_restantes,
                    "fecha_vencimiento": fechas_conservacion['fecha_fin_conservacion'],
                    "razon": f"Derechos vigentes hasta {fechas_conservacion['fecha_fin_conservacion']}"
                }
            else:
                dias_vencidos = (fecha_emision_dt - fecha_fin_conservacion_dt).days
                return {
                    "estado": "VENCIDO",
                    "derechos_conservados": False,
                    "dias_vencidos": dias_vencidos,
                    "fecha_vencimiento": fechas_conservacion['fecha_fin_conservacion'],
                    "razon": f"Derechos vencieron el {fechas_conservacion['fecha_fin_conservacion']}"
                }
        
        except ValueError as e:
            return {
                "estado": "ERROR",
                "derechos_conservados": False,
                "razon": f"Error en cálculo de fechas: {str(e)}"
            }

