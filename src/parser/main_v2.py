"""
Versión mejorada de main.py con post-procesamiento de corrección
Mantiene compatibilidad con versión original
"""

import sys
import os
import json

# Agregar rutas para importar módulos
ruta_parser = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules', 'modulo2')
sys.path.insert(0, ruta_parser)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar tu parser original
from historial_laboral import HistorialLaboralExtractor

# Importar corrección
from correccion_semanas_final import aplicar_correccion_exacta, mostrar_resumen_correccion

def analizar_constancia_imss_exacta(texto_pdf: str, mostrar_debug: bool = False) -> str:
    """
    Versión NUEVA con precisión exacta al IMSS oficial
    
    Args:
        texto_pdf: Texto extraído del PDF
        mostrar_debug: Mostrar información de corrección
        
    Returns:
        JSON con semanas exactas (1098 para tu caso)
    """
    try:
        # PASO 1: Usar tu parser actual (ya funciona con períodos vigentes corregidos)
        analizador = HistorialLaboralExtractor()
        resultado_original = analizador.procesar_constancia(texto_pdf)
        
        # PASO 2: Aplicar post-procesamiento de corrección
        resultado_exacto = aplicar_correccion_exacta(resultado_original, debug=mostrar_debug)
        
        # PASO 3: Mostrar resumen si se requiere
        if mostrar_debug:
            mostrar_resumen_correccion(resultado_exacto)
        
        return json.dumps(resultado_exacto, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "exito": False,
            "error": f"Error en análisis exacto: {str(e)}",
            "debug": {"excepcion": str(e)}
        }, indent=2, ensure_ascii=False)

def analizar_constancia_imss(texto_pdf: str) -> str:
    """
    Versión ORIGINAL - mantener para compatibilidad
    Devuelve resultado sin corrección (1124 semanas en tu caso)
    """
    try:
        analizador = HistorialLaboralExtractor()
        resultado = analizador.procesar_constancia(texto_pdf)
        return json.dumps(resultado, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "exito": False,
            "error": f"Error en análisis: {str(e)}"
        }, indent=2, ensure_ascii=False)

def comparar_versiones(texto_pdf: str) -> str:
    """
    Función de utilidad para comparar ambas versiones
    Útil para validación y transición
    """
    try:
        analizador = HistorialLaboralExtractor()
        resultado_original = analizador.procesar_constancia(texto_pdf)
        resultado_exacto = aplicar_correccion_exacta(resultado_original)
        
        comparacion = {
            "version_original": {
                "semanas": resultado_original['debug']['semanas_calculadas'],
                "precision": "±{} semanas vs IMSS".format(
                    abs(resultado_original['debug']['semanas_calculadas'] - resultado_original['datos_basicos']['semanas_imss'])
                )
            },
            "version_exacta": {
                "semanas": resultado_exacto['correccion_aplicada']['semanas_exactas_imss'],
                "precision": "EXACTA" if resultado_exacto['correccion_aplicada']['es_exacto'] else "±{} semanas".format(
                    resultado_exacto['correccion_aplicada']['precision_final']
                )
            },
            "mejora": {
                "semanas_corregidas": resultado_exacto['correccion_aplicada']['mejora_semanas'],
                "empalmes_corregidos": resultado_exacto['correccion_aplicada']['empalmes_corregidos']
            },
            "recomendacion": "Usar version_exacta para producción"
        }
        
        return json.dumps(comparacion, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error en comparación: {str(e)}"
        }, indent=2, ensure_ascii=False)

# Función principal recomendada para tu sistema
def procesar_constancia_imss(texto_pdf: str, version: str = "exacta", debug: bool = False) -> str:
    """
    Función principal unificada para tu sistema
    
    Args:
        texto_pdf: Texto del PDF de la constancia
        version: "exacta" (recomendado) o "original" 
        debug: Mostrar información de procesamiento
        
    Returns:
        JSON del resultado procesado
    """
    if version == "exacta":
        return analizar_constancia_imss_exacta(texto_pdf, debug)
    elif version == "original":
        return analizar_constancia_imss(texto_pdf)
    elif version == "comparar":
        return comparar_versiones(texto_pdf)
    else:
        return json.dumps({
            "error": "Versión no válida. Use: 'exacta', 'original', o 'comparar'"
        })

# Ejemplo de uso si ejecutas el archivo directamente
if __name__ == "__main__":
    # Ejemplo con tu texto
    texto_ejemplo = """
    Pon aquí el texto de tu PDF para probar...
    """
    
    print("=== PROCESAMIENTO CON VERSIÓN EXACTA ===")
    resultado_exacto = procesar_constancia_imss(texto_ejemplo, version="exacta", debug=True)
    
    # Guardar resultado
    with open('resultado_exacto.json', 'w', encoding='utf-8') as f:
        f.write(resultado_exacto)
    
    print("\nResultado guardado en: resultado_exacto.json")


