"""
Calculador del promedio salarial de las últimas 250 semanas cotizadas
Implementa las reglas específicas del IMSS para Ley 73
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math

class PromedioSalario250:
    
    def __init__(self):
        self.dias_250_semanas = 1750  # 250 semanas * 7 días
        self.topes_uma_historicos = {
            # Topes diarios de 25 UMA por año
            2025: 2826.5,    # 25 * 113.14 
            2024: 2743.75,   # 25 * 109.75
            2023: 2671.25,   # 25 * 106.85
            2022: 2598.75,   # 25 * 103.95
            2021: 2526.25,   # 25 * 101.05
            2020: 2453.75,   # 25 * 98.15
            2019: 2381.25,   # 25 * 95.25
            2018: 2308.75,   # 25 * 92.35
            2017: 2236.25,   # 25 * 89.45
            2016: 2163.75,   # 25 * 86.55
            2015: 2091.25,   # 25 * 83.65
        }
    
    def calcular_promedio_250_semanas(self, periodos_depurados: List[Dict[str, Any]], 
                                    fecha_referencia: str, ley_aplicable: str) -> Dict[str, Any]:
        """
        Calcula el salario promedio de las últimas 250 semanas cotizadas
        
        Args:
            periodos_depurados: Períodos laborales ya depurados (sin traslapes)
            fecha_referencia: Fecha de emisión del reporte
            ley_aplicable: "Ley 73" o "Ley 97"
        
        Returns:
            Dict con el cálculo detallado del promedio
        """
        if ley_aplicable != "Ley 73":
            return {
                "error": "Este calculador es específico para Ley 73",
                "ley_detectada": ley_aplicable
            }
        
        # Convertir fecha de referencia
        fecha_ref_dt = datetime.strptime(fecha_referencia, '%Y-%m-%d')
        
        # Identificar las últimas 250 semanas (1750 días)
        fecha_inicio_250 = fecha_ref_dt - timedelta(days=self.dias_250_semanas - 1)
        
        # Construir serie diaria de salarios
        serie_salarios = self._construir_serie_diaria(
            periodos_depurados, fecha_inicio_250, fecha_ref_dt
        )
        
        # Calcular promedio
        promedio_calculado = self._calcular_promedio_ponderado(serie_salarios)
        
        # Generar reporte detallado
        return {
            "exito": True,
            "ley_aplicable": ley_aplicable,
            "fecha_referencia": fecha_referencia,
            "periodo_calculo": {
                "fecha_inicio": fecha_inicio_250.strftime('%Y-%m-%d'),
                "fecha_fin": fecha_ref_dt.strftime('%Y-%m-%d'),
                "dias_calculados": len(serie_salarios),
                "dias_esperados": self.dias_250_semanas
            },
            "salario_promedio_diario": round(promedio_calculado, 2),
            "salario_promedio_mensual": round(promedio_calculado * 30.4, 2),
            "salario_promedio_anual": round(promedio_calculado * 365, 2),
            "detalle_calculo": self._generar_detalle_periodos(serie_salarios, periodos_depurados),
            "topes_aplicados": self._identificar_topes_aplicados(serie_salarios),
            "estadisticas": {
                "salario_minimo": min([s['salario'] for s in serie_salarios]) if serie_salarios else 0,
                "salario_maximo": max([s['salario'] for s in serie_salarios]) if serie_salarios else 0,
                "periodos_utilizados": len(set([s['periodo_id'] for s in serie_salarios])),
                "dias_con_tope": sum(1 for s in serie_salarios if s.get('tope_aplicado', False))
            }
        }
    
    def _construir_serie_diaria(self, periodos: List[Dict[str, Any]], 
                               fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict[str, Any]]:
        """
        Construye una serie diaria de salarios para las últimas 250 semanas
        """
        serie_salarios = []
        
        # Ordenar períodos por fecha de inicio
        periodos_ordenados = sorted(periodos, key=lambda x: x['fecha_inicio_dt'])
        
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            # Encontrar período(s) activo(s) para esta fecha
            periodos_activos = self._encontrar_periodos_activos(periodos_ordenados, current_date)
            
            if periodos_activos:
                # Usar el salario ya depurado (suma de traslapes ya aplicada)
                periodo_activo = periodos_activos[0]  # Ya depurado, solo debería haber uno
                salario_dia = periodo_activo['salario_diario']
                
                # Aplicar tope histórico si es necesario
                year = current_date.year
                tope_diario = self.topes_uma_historicos.get(year, 2000.0)  # Default
                
                salario_final = min(salario_dia, tope_diario)
                tope_aplicado = salario_dia > tope_diario
                
                serie_salarios.append({
                    'fecha': current_date,
                    'salario': salario_final,
                    'salario_original': salario_dia,
                    'tope_aplicado': tope_aplicado,
                    'tope_usado': tope_diario,
                    'periodo_id': id(periodo_activo),
                    'patron': periodo_activo.get('patron', 'N/A'),
                    'registro_patronal': periodo_activo.get('registro_patronal', 'N/A')
                })
            else:
                # Día sin empleo registrado
                serie_salarios.append({
                    'fecha': current_date,
                    'salario': 0,
                    'salario_original': 0,
                    'tope_aplicado': False,
                    'tope_usado': 0,
                    'periodo_id': None,
                    'patron': 'Sin empleo',
                    'registro_patronal': 'N/A'
                })
            
            current_date += timedelta(days=1)
        
        return serie_salarios
    
    def _encontrar_periodos_activos(self, periodos: List[Dict[str, Any]], fecha: datetime) -> List[Dict[str, Any]]:
        """Encuentra los períodos activos para una fecha específica"""
        activos = []
        
        for periodo in periodos:
            fecha_inicio = periodo['fecha_inicio_dt']
            fecha_fin = periodo['fecha_fin_dt']
            
            # Verificar si la fecha está dentro del período
            if fecha_fin is None:  # Empleo vigente
                if fecha >= fecha_inicio:
                    activos.append(periodo)
            else:
                if fecha_inicio <= fecha <= fecha_fin:
                    activos.append(periodo)
        
        return activos
    
    def _calcular_promedio_ponderado(self, serie_salarios: List[Dict[str, Any]]) -> float:
        """Calcula el promedio ponderado de los salarios"""
        if not serie_salarios:
            return 0.0
        
        suma_salarios = sum(s['salario'] for s in serie_salarios)
        dias_calculados = len(serie_salarios)
        
        return suma_salarios / dias_calculados if dias_calculados > 0 else 0.0
    
    def _generar_detalle_periodos(self, serie_salarios: List[Dict[str, Any]], 
                                 periodos_originales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Genera un detalle de los períodos utilizados en el cálculo"""
        detalle = []
        
        # Agrupar por período para el detalle
        periodos_usados = {}
        
        for salario_dia in serie_salarios:
            periodo_id = salario_dia['periodo_id']
            if periodo_id and periodo_id not in periodos_usados:
                # Encontrar el período original
                periodo_original = next((p for p in periodos_originales if id(p) == periodo_id), None)
                if periodo_original:
                    dias_usados = sum(1 for s in serie_salarios if s['periodo_id'] == periodo_id)
                    salario_promedio_periodo = sum(s['salario'] for s in serie_salarios if s['periodo_id'] == periodo_id) / dias_usados
                    
                    periodos_usados[periodo_id] = {
                        "patron": periodo_original['patron'],
                        "registro_patronal": periodo_original['registro_patronal'],
                        "fecha_inicio": periodo_original['fecha_inicio'],
                        "fecha_fin": periodo_original.get('fecha_fin', 'VIGENTE'),
                        "salario_diario_original": periodo_original['salario_diario'],
                        "salario_diario_promedio_usado": round(salario_promedio_periodo, 2),
                        "dias_utilizados_calculo": dias_usados,
                        "contribucion_total": round(salario_promedio_periodo * dias_usados, 2)
                    }
        
        return list(periodos_usados.values())
    
    def _identificar_topes_aplicados(self, serie_salarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identifica cuándo y dónde se aplicaron topes salariales"""
        topes_aplicados = {}
        
        for salario_dia in serie_salarios:
            if salario_dia['tope_aplicado']:
                year = salario_dia['fecha'].year
                if year not in topes_aplicados:
                    topes_aplicados[year] = {
                        "tope_diario": salario_dia['tope_usado'],
                        "dias_afectados": 0,
                        "diferencia_total": 0
                    }
                
                topes_aplicados[year]["dias_afectados"] += 1
                topes_aplicados[year]["diferencia_total"] += (
                    salario_dia['salario_original'] - salario_dia['salario']
                )
        
        return topes_aplicados


