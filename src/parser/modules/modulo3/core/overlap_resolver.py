"""
Resolvedor de traslapes entre empleos múltiples
Aplica las reglas del IMSS para manejar empleos simultáneos y traslapes
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

class OverlapResolver:
    
    def __init__(self):
        self.topes_uma = {
            # Topes históricos de 25 UMA por año
            2025: 1031838.0,  # 25 * 113.14 * 365
            2024: 1000000.0,  # Aproximado
            2023: 950000.0,
            2022: 900000.0,
            2021: 850000.0,
            2020: 800000.0,
            # Agregar más años según necesidad
        }
    
    def resolve_overlaps(self, periodos: List[Dict[str, Any]], fecha_emision: str) -> List[Dict[str, Any]]:
        """
        Resuelve traslapes aplicando reglas del IMSS
        1. Suma salarios hasta tope 25 UMA por año
        2. Maneja empleos vigentes como últimos empleos
        3. Elimina períodos duplicados o inconsistentes
        """
        # Convertir fechas string a datetime para cálculos
        periodos_procesados = self._prepare_periods(periodos)
        
        # Detectar y resolver traslapes
        periodos_resueltos = self._resolve_salary_overlaps(periodos_procesados)
        
        # Ajustar empleos vigentes a fecha de emisión
        periodos_ajustados = self._adjust_vigentes(periodos_resueltos, fecha_emision)
        
        # Eliminar duplicados y consolidar
        periodos_consolidados = self._consolidate_periods(periodos_ajustados)
        
        return periodos_consolidados
    
    def _prepare_periods(self, periodos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepara los períodos convirtiendo fechas y validando datos"""
        prepared = []
        
        for periodo in periodos:
            try:
                # Convertir fechas
                fecha_inicio = datetime.strptime(periodo['fecha_inicio'], '%d/%m/%Y')
                
                if periodo.get('esta_vigente', False):
                    fecha_fin = None
                else:
                    fecha_fin = datetime.strptime(periodo['fecha_fin'], '%d/%m/%Y')
                
                periodo_preparado = {
                    **periodo,
                    'fecha_inicio_dt': fecha_inicio,
                    'fecha_fin_dt': fecha_fin,
                    'salario_diario': float(periodo.get('salario_diario', 0)),
                    'año_inicio': fecha_inicio.year
                }
                
                prepared.append(periodo_preparado)
                
            except (ValueError, KeyError) as e:
                # Log error pero continúa procesando
                continue
        
        return prepared
    
    def _resolve_salary_overlaps(self, periodos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resuelve traslapes de salarios aplicando tope de 25 UMA
        """
        # Agrupar períodos por fecha para detectar traslapes
        periods_by_date = defaultdict(list)
        
        for periodo in periodos:
            fecha_inicio = periodo['fecha_inicio_dt']
            fecha_fin = periodo['fecha_fin_dt']
            
            # Generar días del período
            current_date = fecha_inicio
            while fecha_fin is None or current_date <= fecha_fin:
                periods_by_date[current_date].append(periodo)
                current_date += timedelta(days=1)
                
                # Para empleos vigentes, solo procesar hasta una fecha límite
                if fecha_fin is None and (current_date - fecha_inicio).days > 3650:  # Máximo 10 años
                    break
        
        # Procesar traslapes por día
        resolved_periods = []
        processed_periods = set()
        
        for periodo in periodos:
            if id(periodo) in processed_periods:
                continue
            
            # Verificar si tiene traslapes
            overlapping_periods = self._find_overlapping_periods(periodo, periodos)
            
            if len(overlapping_periods) > 1:
                # Resolver traslape sumando salarios hasta tope
                resolved_period = self._merge_overlapping_periods(overlapping_periods)
                resolved_periods.append(resolved_period)
                
                # Marcar períodos como procesados
                for p in overlapping_periods:
                    processed_periods.add(id(p))
            else:
                resolved_periods.append(periodo)
                processed_periods.add(id(periodo))
        
        return resolved_periods
    
    def _find_overlapping_periods(self, periodo: Dict[str, Any], all_periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encuentra períodos que se traslapan con el período dado"""
        overlapping = [periodo]
        
        inicio1 = periodo['fecha_inicio_dt']
        fin1 = periodo['fecha_fin_dt']
        
        for other in all_periods:
            if id(other) == id(periodo):
                continue
                
            inicio2 = other['fecha_inicio_dt']
            fin2 = other['fecha_fin_dt']
            
            # Verificar traslape
            if self._periods_overlap(inicio1, fin1, inicio2, fin2):
                overlapping.append(other)
        
        return overlapping
    
    def _periods_overlap(self, inicio1, fin1, inicio2, fin2) -> bool:
        """Verifica si dos períodos se traslapan"""
        # Manejar empleos vigentes (fin = None)
        if fin1 is None:
            fin1 = datetime.now()
        if fin2 is None:
            fin2 = datetime.now()
        
        return not (fin1 < inicio2 or fin2 < inicio1)
    
    def _merge_overlapping_periods(self, overlapping_periods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusiona períodos traslapados aplicando regla de suma de salarios hasta tope UMA
        """
        if len(overlapping_periods) == 1:
            return overlapping_periods[0]
        
        # Ordenar por fecha de inicio
        sorted_periods = sorted(overlapping_periods, key=lambda x: x['fecha_inicio_dt'])
        base_period = sorted_periods[0].copy()
        
        # Sumar salarios
        total_salary = 0
        year = base_period['año_inicio']
        tope_anual = self.topes_uma.get(year, 800000.0)  # Default si no se encuentra el año
        tope_diario = tope_anual / 365
        
        for periodo in overlapping_periods:
            total_salary += periodo['salario_diario']
        
        # Aplicar tope de 25 UMA
        salary_final = min(total_salary, tope_diario)
        
        # Actualizar período base
        base_period.update({
            'salario_diario': salary_final,
            'salario_original': total_salary,
            'tope_aplicado': total_salary > tope_diario,
            'periodos_fusionados': len(overlapping_periods),
            'patrones_fusionados': [p['patron'] for p in overlapping_periods]
        })
        
        return base_period
    
    def _adjust_vigentes(self, periodos: List[Dict[str, Any]], fecha_emision: str) -> List[Dict[str, Any]]:
        """
        Ajusta empleos vigentes para que su fecha fin sea igual a la fecha de emisión
        """
        fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%d')
        
        adjusted = []
        for periodo in periodos:
            if periodo.get('esta_vigente', False):
                periodo_ajustado = periodo.copy()
                periodo_ajustado['fecha_fin'] = fecha_emision
                periodo_ajustado['fecha_fin_dt'] = fecha_emision_dt
                periodo_ajustado['es_ultimo_empleo'] = True
                adjusted.append(periodo_ajustado)
            else:
                adjusted.append(periodo)
        
        return adjusted
    
    def _consolidate_periods(self, periodos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolida períodos eliminando duplicados y ordenando por fecha
        """
        # Eliminar duplicados basados en patrón y fechas
        unique_periods = []
        seen = set()
        
        for periodo in periodos:
            key = (
                periodo.get('registro_patronal', ''),
                periodo['fecha_inicio'],
                periodo.get('fecha_fin', 'VIGENTE')
            )
            
            if key not in seen:
                unique_periods.append(periodo)
                seen.add(key)
        
        # Ordenar por fecha de inicio (más reciente primero)
        return sorted(unique_periods, key=lambda x: x['fecha_inicio_dt'], reverse=True)


