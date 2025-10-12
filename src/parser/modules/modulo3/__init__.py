"""
Módulo 3 - Cálculo de Pensiones IMSS
Procesamiento completo de pensiones con validación de calidad
"""
from .pension_processor import PensionProcessor, procesar_pension_imss

__all__ = ['PensionProcessor', 'procesar_pension_imss']
__version__ = '1.0.0'
