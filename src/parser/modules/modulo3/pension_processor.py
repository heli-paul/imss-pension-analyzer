"""
Procesador principal del Módulo 3 - Cálculo de Pensiones IMSS
Coordina todos los cálculos y validaciones
"""

from typing import Dict, Any
import json
from datetime import datetime

# Importar componentes del módulo
from .core.quality_validator import QualityValidator
from .core.overlap_resolver import OverlapResolver
from .calculators.promedio_250 import PromedioSalario250
from .calculators.conservacion_derechos import ConservacionDerechos
from .validators.cross_validator import CrossValidator
from .validators.final_quality import FinalQuality

class PensionProcessor:
    """
    Procesador principal que coordina todos los cálculos de pensión
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # Inicializar componentes
        self.quality_validator = QualityValidator()
        self.overlap_resolver = OverlapResolver()
        self.promedio_calculator = PromedioSalario250()
        self.conservacion_calculator = ConservacionDerechos()
        self.cross_validator = CrossValidator()
        self.final_quality = FinalQuality()
    
    def procesar_pension_completa(self, datos_parser: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa completamente los cálculos de pensión desde el output del parser
        
        Args:
            datos_parser: Output completo del parser (datos_basicos + historial_laboral + debug)
        
        Returns:
            Dict con todos los cálculos de pensión
        """
        try:
            # Extraer secciones del parser
            datos_basicos = datos_parser.get('datos_basicos', {})
            historial_laboral = datos_parser.get('historial_laboral', {})
            debug_info = datos_parser.get('debug', {})
            
            # 1. Validación inicial de calidad
            quality_result = self.quality_validator.evaluate_extraction_quality(
                datos_basicos, debug_info
            )
            
            can_proceed, quality_message = self.quality_validator.can_proceed_with_calculation(quality_result)
            
            if not can_proceed:
                return {
                    "exito": False,
                    "error": "Calidad de extracción insuficiente",
                    "detalle": quality_message,
                    "quality_assessment": quality_result
                }
            
            # 2. Depuración de períodos laborales (resolver traslapes)
            periodos_originales = historial_laboral.get('periodos', [])
            fecha_emision = datos_basicos.get('fecha_emision')
            
            periodos_depurados = self.overlap_resolver.resolve_overlaps(
                periodos_originales, fecha_emision
            )
            
            # 3. Cálculo de promedio de 250 semanas (Ruta 1)
            ley_aplicable = datos_basicos.get('ley_aplicable', 'No determinada')
            
            if ley_aplicable == "Ley 73":
                calculo_250_semanas = self.promedio_calculator.calcular_promedio_250_semanas(
                    periodos_depurados, fecha_emision, ley_aplicable
                )
            else:
                calculo_250_semanas = {
                    "error": "Cálculo de 250 semanas solo disponible para Ley 73",
                    "ley_detectada": ley_aplicable,
                    "nota": "Para Ley 97 se usa el cálculo de cuenta individual"
                }
            
            # 4. Cálculo de conservación de derechos (Ruta 2)
            conservacion_derechos = self.conservacion_calculator.calcular_conservacion_derechos(
                datos_basicos, {'periodos': periodos_depurados}
            )
            
            # 5. Validación cruzada entre ambas rutas
            validacion_cruzada = self.cross_validator.validate_cross_calculations(
                calculo_250_semanas, conservacion_derechos, datos_basicos
            )
            
            # 6. Evaluación final de calidad
            calidad_final = self.final_quality.evaluate_final_quality(
                quality_result, calculo_250_semanas, conservacion_derechos, validacion_cruzada
            )
            
            # 7. Construir resultado final
            resultado_completo = {
                "exito": True,
                "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "archivo_procesado": datos_parser.get('archivo', 'N/A'),
                "asegurado": {
                    "nombre": datos_basicos.get('nombre', 'N/A'),
                    "nss": datos_basicos.get('nss', 'N/A'),
                    "curp": datos_basicos.get('curp', 'N/A')
                },
                "quality_assessment": quality_result,
                "depuracion_periodos": {
                    "periodos_originales": len(periodos_originales),
                    "periodos_depurados": len(periodos_depurados),
                    "traslapes_resueltos": len(periodos_originales) - len(periodos_depurados),
                    "empleos_vigentes_detectados": sum(1 for p in periodos_depurados if p.get('esta_vigente', False))
                },
                "ruta_1_promedio_250_semanas": calculo_250_semanas,
                "ruta_2_conservacion_derechos": conservacion_derechos,
                "validacion_cruzada": validacion_cruzada,
                "calidad_final": calidad_final,
                "debug_info": {
                    "modo_debug": self.debug_mode,
                    "componentes_ejecutados": [
                        "quality_validator",
                        "overlap_resolver", 
                        "promedio_calculator",
                        "conservacion_calculator",
                        "cross_validator",
                        "final_quality"
                    ]
                } if self.debug_mode else {}
            }
            
            return resultado_completo
            
        except Exception as e:
            return {
                "exito": False,
                "error": f"Error durante procesamiento: {str(e)}",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "debug_info": {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                } if self.debug_mode else {}
            }

# Función de conveniencia para uso directo
def procesar_pension_imss(datos_parser_json: str, debug_mode: bool = False) -> str:
    """
    Función de conveniencia que procesa JSON del parser y devuelve JSON resultado
    
    Args:
        datos_parser_json: JSON string con output del parser
        debug_mode: Si incluir información de debug
    
    Returns:
        JSON string con resultados de pensión
    """
    try:
        # Parsear JSON de entrada
        datos_parser = json.loads(datos_parser_json)
        
        # Procesar
        processor = PensionProcessor(debug_mode=debug_mode)
        resultado = processor.procesar_pension_completa(datos_parser)
        
        # Devolver como JSON
        return json.dumps(resultado, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        error_result = {
            "exito": False,
            "error": f"Error al parsear JSON de entrada: {str(e)}",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


