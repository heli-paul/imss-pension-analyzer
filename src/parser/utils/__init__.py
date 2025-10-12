"""
Reglas oficiales IMSS según Lineamientos para Certificación de Pensiones
Artículos 150 LSS 97 / 182 LSS 73
"""
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def validar_conservacion_derechos_52_semanas(semanas_ultimos_5_anos):
    """
    Regla crítica: Mínimo 52 semanas en últimos 5 años
    Artículos 150 LSS 97 / 182 LSS 73
    """
    return semanas_ultimos_5_anos >= 52

def calcular_fecha_conservacion_oficial(total_semanas, fecha_baja):
    """
    Fórmula oficial IMSS: (semanas × 7 días) ÷ 4
    Mínimo: 365 días (12 meses)
    """
    try:
        # Convertir fecha_baja si es string
        if isinstance(fecha_baja, str):
            if '/' in fecha_baja:
                fecha_baja_obj = datetime.strptime(fecha_baja, '%d/%m/%Y')
            else:
                fecha_baja_obj = datetime.strptime(fecha_baja, '%Y-%m-%d')
        else:
            fecha_baja_obj = fecha_baja
            
        # Fórmula oficial IMSS
        dias_calculados = (total_semanas * 7) / 4
        
        # Mínimo 365 días según lineamientos
        dias_conservacion = max(365, dias_calculados)
        
        # Redondeo según lineamientos: < 0.6 hacia abajo, >= 0.6 hacia arriba
        dias_enteros = int(dias_calculados)
        fraccion = dias_calculados - dias_enteros
        
        if fraccion < 0.6:
            dias_finales = dias_enteros
        else:
            dias_finales = dias_enteros + 1
            
        dias_finales = max(365, dias_finales)
        
        # Calcular fecha de conservación
        fecha_conservacion = fecha_baja_obj + timedelta(days=dias_finales)
        
        logger.info(f"Cálculo conservación: {total_semanas} sem → {dias_calculados:.1f} días → {dias_finales} días")
        
        return fecha_conservacion, dias_finales
        
    except Exception as e:
        logger.error(f"Error calculando fecha conservación: {e}")
        return None, 0

def determinar_estado_conservacion(semanas_ultimos_5_anos, fecha_conservacion, fecha_actual=None):
    """
    Determina estado final de conservación aplicando todas las reglas
    """
    if fecha_actual is None:
        fecha_actual = datetime.now()
        
    observaciones = []
    
    # REGLA 1: Verificar 52 semanas mínimas
    cumple_52_semanas = validar_conservacion_derechos_52_semanas(semanas_ultimos_5_anos)
    
    if not cumple_52_semanas:
        return {
            'conserva_derechos': False,
            'cumple_requisitos': False,
            'observaciones': [f"No cumple requisito mínimo de 52 semanas en últimos 5 años ({semanas_ultimos_5_anos} semanas)"]
        }
    
    # REGLA 2: Verificar si fecha conservación no ha expirado
    if isinstance(fecha_conservacion, str):
        if '/' in fecha_conservacion:
            fecha_conservacion_obj = datetime.strptime(fecha_conservacion, '%d/%m/%Y')
        else:
            fecha_conservacion_obj = datetime.strptime(fecha_conservacion, '%Y-%m-%d')
    else:
        fecha_conservacion_obj = fecha_conservacion
    
    conserva_por_fecha = fecha_actual <= fecha_conservacion_obj
    
    if conserva_por_fecha:
        observaciones.append(f"Conserva derechos hasta {fecha_conservacion_obj.strftime('%d/%m/%Y')}")
    else:
        observaciones.append(f"Perdió derechos el {fecha_conservacion_obj.strftime('%d/%m/%Y')}")
    
    return {
        'conserva_derechos': conserva_por_fecha and cumple_52_semanas,
        'cumple_requisitos': cumple_52_semanas,
        'observaciones': observaciones
    }

