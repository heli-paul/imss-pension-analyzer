# verificar_cambio.py
import sys
import os

# Agregar paths
ruta_parser = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules', 'modulo2')
sys.path.insert(0, ruta_parser)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from historial_laboral import HistorialLaboralExtractor
from correccion_semanas_final import aplicar_correccion_exacta

# Simular tu flujo actual
def probar_flujo_modificado():
    # JSON de entrada simulado (como si viniera del PDF)
    resultado_base = {
        "datos_basicos": {"semanas_imss": 1098, "fecha_emision": "2025-06-17"},
        "historial_laboral": {"periodos": []},  # Simplificado para test
        "debug": {"semanas_calculadas": 1124}
    }
    
    print("ANTES de corrección:")
    print(f"  Semanas: {resultado_base['debug']['semanas_calculadas']}")
    
    # Aplicar tu modificación
    resultado_final = aplicar_correccion_exacta(resultado_base)
    
    print("DESPUÉS de corrección:")
    print(f"  Semanas: {resultado_final['correccion_aplicada']['semanas_exactas_imss']}")
    
    return resultado_final

if __name__ == "__main__":
    probar_flujo_modificado()

