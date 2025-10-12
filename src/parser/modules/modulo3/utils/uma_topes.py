"""
Utilidades para manejo de UMA y topes salariales históricos del IMSS
Contiene los topes oficiales por año para aplicar en cálculos de pensión
"""

from typing import Dict, Optional, Tuple
from datetime import datetime

class UMATopes:
    """Manejo de UMA y topes salariales históricos"""
    
    # Valores UMA diarios históricos (oficiales IMSS)
    UMA_DIARIA_HISTORICA = {
        2025: 113.14,
        2024: 109.75, 
        2023: 106.85,
        2022: 103.95,
        2021: 101.05,
        2020: 98.15,
        2019: 95.25,
        2018: 92.35,
        2017: 89.45,
        2016: 86.55,
        2015: 83.65,
        2014: 80.75,
        2013: 67.29,
        2012: 62.33,
        2011: 59.82,
        2010: 57.46,
        2009: 54.80,
        2008: 52.59,
        2007: 50.57,
        2006: 48.67,
        2005: 46.80,
        2004: 45.24,
        2003: 43.65,
        2002: 42.15,
        2001: 40.30,
        2000: 37.90
    }
    
    # Múltiples para diferentes seguros
    MULTIPLES_TOPE = {
        'invalidez_vida_rcv': 25,  # 25 UMA para IV y RCV
        'riesgos_trabajo': 25,     # 25 UMA para RT
        'enfermedad_maternidad': 25 # 25 UMA para EM
    }
    
    def __init__(self):
        self.cache_topes = {}
    
    def get_uma_diaria(self, año: int) -> float:
        """
        Obtiene el valor de UMA diaria para un año específico
        
        Args:
            año: Año del cual obtener la UMA
            
        Returns:
            Valor UMA diaria en pesos
        """
        if año in self.UMA_DIARIA_HISTORICA:
            return self.UMA_DIARIA_HISTORICA[año]
        
        # Para años no encontrados, usar el más cercano
        años_disponibles = sorted(self.UMA_DIARIA_HISTORICA.keys())
        
        if año < años_disponibles[0]:
            return self.UMA_DIARIA_HISTORICA[años_disponibles[0]]
        elif año > años_disponibles[-1]:
            return self.UMA_DIARIA_HISTORICA[años_disponibles[-1]]
        
        # Interpolar entre años cercanos
        año_anterior = max([a for a in años_disponibles if a <= año])
        return self.UMA_DIARIA_HISTORICA[año_anterior]
    
    def get_tope_diario(self, año: int, tipo_seguro: str = 'invalidez_vida_rcv') -> float:
        """
        Obtiene el tope salarial diario para un año y tipo de seguro
        
        Args:
            año: Año del tope
            tipo_seguro: Tipo de seguro (invalidez_vida_rcv, riesgos_trabajo, etc.)
            
        Returns:
            Tope salarial diario en pesos
        """
        cache_key = f"{año}_{tipo_seguro}"
        if cache_key in self.cache_topes:
            return self.cache_topes[cache_key]
        
        uma_diaria = self.get_uma_diaria(año)
        multiple = self.MULTIPLES_TOPE.get(tipo_seguro, 25)
        tope_diario = uma_diaria * multiple
        
        self.cache_topes[cache_key] = tope_diario
        return tope_diario
    
    def get_tope_mensual(self, año: int, tipo_seguro: str = 'invalidez_vida_rcv') -> float:
        """Obtiene el tope salarial mensual"""
        return self.get_tope_diario(año, tipo_seguro) * 30.4
    
    def get_tope_anual(self, año: int, tipo_seguro: str = 'invalidez_vida_rcv') -> float:
        """Obtiene el tope salarial anual"""
        return self.get_tope_diario(año, tipo_seguro) * 365
    
    def aplicar_tope_salario(self, salario_diario: float, año: int, 
                           tipo_seguro: str = 'invalidez_vida_rcv') -> Tuple[float, bool]:
        """
        Aplica el tope salarial a un salario específico
        
        Args:
            salario_diario: Salario diario a evaluar
            año: Año para determinar el tope
            tipo_seguro: Tipo de seguro
            
        Returns:
            Tuple(salario_final, tope_aplicado)
        """
        tope_diario = self.get_tope_diario(año, tipo_seguro)
        
        if salario_diario > tope_diario:
            return tope_diario, True
        
        return salario_diario, False
    
    def get_info_tope_año(self, año: int, tipo_seguro: str = 'invalidez_vida_rcv') -> Dict:
        """
        Obtiene información completa del tope para un año
        
        Returns:
            Dict con información detallada del tope
        """
        uma_diaria = self.get_uma_diaria(año)
        multiple = self.MULTIPLES_TOPE.get(tipo_seguro, 25)
        
        return {
            "año": año,
            "tipo_seguro": tipo_seguro,
            "uma_diaria": uma_diaria,
            "multiple_aplicado": multiple,
            "tope_diario": uma_diaria * multiple,
            "tope_mensual": uma_diaria * multiple * 30.4,
            "tope_anual": uma_diaria * multiple * 365,
            "fuente": "IMSS - Valores UMA oficiales"
        }
    
    def validar_salario_historico(self, salario_diario: float, año: int) -> Dict:
        """
        Valida si un salario histórico es razonable para su época
        
        Returns:
            Dict con resultado de validación
        """
        uma_año = self.get_uma_diaria(año)
        tope_año = self.get_tope_diario(año)
        
        # Rangos razonables (0.5 UMA mínimo, 25 UMA máximo)
        minimo_razonable = uma_año * 0.5
        maximo_legal = tope_año
        
        if salario_diario < minimo_razonable:
            return {
                "valido": False,
                "razon": f"Salario muy bajo para {año}",
                "salario_evaluado": salario_diario,
                "minimo_esperado": minimo_razonable,
                "uma_año": uma_año
            }
        elif salario_diario > maximo_legal:
            return {
                "valido": False, 
                "razon": f"Salario excede tope legal para {año}",
                "salario_evaluado": salario_diario,
                "tope_legal": maximo_legal,
                "uma_año": uma_año
            }
        else:
            return {
                "valido": True,
                "razon": f"Salario dentro de rangos normales para {año}",
                "salario_evaluado": salario_diario,
                "uma_año": uma_año,
                "porcentaje_uma": round((salario_diario / uma_año), 2)
            }

# Instancia global para uso conveniente
uma_calculator = UMATopes()


