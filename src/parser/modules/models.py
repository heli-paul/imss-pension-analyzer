"""
Modelos Pydantic compartidos entre módulos
"""

from pydantic import BaseModel
from typing import Optional, List, Dict

class PeriodoLaboral(BaseModel):
    empresa: str
    registro_patronal: str
    entidad_federativa: str
    fecha_alta: str
    fecha_baja: Optional[str]
    salario_base: float
    vigente: bool

class MovimientoSalario(BaseModel):
    tipo_movimiento: str
    fecha: str
    salario_diario: float
    empresa: Optional[str] = ""
    registro_patronal: Optional[str] = ""

class ConservacionDerechos(BaseModel):
    conserva_derechos: bool
    fecha_conservacion: Optional[str] = None
    fecha_ultima_baja: Optional[str] = None
    periodo_conservacion_meses: Optional[int] = None
    semanas_ultimos_5_anos: Optional[int] = None
    cumple_requisitos: bool = False
    observaciones: List[str] = []

class ResultadoParsing(BaseModel):
    archivo: str
    resumen: Optional[Dict] = None
    nss: Optional[str] = None
    curp: Optional[str] = None
    nombre: Optional[str] = None
    fecha_emision: Optional[str] = None
    semanas_cotizadas: Optional[int] = None
    semanas_imss: Optional[int] = None
    semanas_descontadas: Optional[int] = None
    semanas_reintegradas: Optional[int] = None
    total_semanas: Optional[int] = None
    periodos_laborales: List[PeriodoLaboral] = []
    movimientos_salario: List[MovimientoSalario] = []
    promedio_250_semanas: Optional[float] = None
    semanas_para_calculo: Optional[int] = None
    conservacion_derechos: Optional[ConservacionDerechos] = None
    errors: List[str] = []


