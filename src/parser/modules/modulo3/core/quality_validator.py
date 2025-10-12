"""
Validador de calidad para el historial laboral extraído
Compara semanas calculadas vs semanas IMSS para determinar precisión de extracción
"""

from typing import Dict, Any, Tuple

class QualityValidator:
    
    def __init__(self):
        self.tolerance_high = 5  # Tolerancia para calidad ALTA
        
    def evaluate_extraction_quality(self, datos_basicos: Dict[str, Any], debug_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa la calidad de extracción comparando semanas calculadas vs IMSS
        
        Returns:
            Dict con calidad, diferencia, confianza y recomendaciones
        """
        semanas_imss = datos_basicos.get('semanas_imss', 0)
        semanas_calculadas = debug_info.get('semanas_calculadas', 0)
        
        diferencia = semanas_calculadas - semanas_imss
        
        # Determinar calidad
        if diferencia < 0:
            calidad = "BAJA"
            confianza = "BAJO"
            razon = "Faltan períodos laborales en la extracción"
        elif abs(diferencia) <= self.tolerance_high:
            calidad = "ALTA"
            confianza = "ALTO"
            razon = "Extracción muy precisa, diferencia mínima"
        else:  # diferencia > 0
            calidad = "BUENA"
            confianza = "MEDIO"
            razon = "Extracción completa, sin pérdida de datos"
        
        return {
            "calidad_extraccion": calidad,
            "confianza": confianza,
            "semanas_imss": semanas_imss,
            "semanas_calculadas": semanas_calculadas,
            "diferencia": diferencia,
            "razon": razon,
            "requiere_depuracion": diferencia != 0,
            "porcentaje_precision": round((min(semanas_imss, semanas_calculadas) / max(semanas_imss, semanas_calculadas)) * 100, 2) if max(semanas_imss, semanas_calculadas) > 0 else 0
        }
    
    def can_proceed_with_calculation(self, quality_result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determina si se puede proceder con los cálculos basado en la calidad
        
        Returns:
            Tuple(puede_proceder, mensaje)
        """
        calidad = quality_result.get('calidad_extraccion')
        diferencia = quality_result.get('diferencia', 0)
        
        if calidad == "BAJA":
            return False, "Calidad de extracción insuficiente. Faltan períodos laborales."
        
        if abs(diferencia) > 50:  # Diferencia muy grande
            return False, f"Diferencia excesiva: {diferencia} semanas. Requiere revisión manual."
        
        return True, f"Calidad {calidad}: Se puede proceder con los cálculos."


