"""
Módulo para calcular la conservación de derechos IMSS
Implementa las reglas para Ley 73 y Ley 97 según el Artículo 150 y 191 respectivamente.
VERSIÓN MODIFICADA: Incluye fechas hipotéticas para trabajadores vigentes

COORDINA CON: correccion_semanas_final.py
USO: from conservacion_derechos import CalculadoraConservacionDerechos
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ResultadoConservacion:
    """Resultado del cálculo de conservación de derechos"""
    ley_aplicable: str  # "Ley 73" o "Ley 97"
    semanas_reconocidas: int
    años_cotizados: float
    conservacion_años: float
    conservacion_dias: int
    fecha_ultima_baja: Optional[datetime]
    fecha_vencimiento: Optional[datetime]
    esta_vigente: bool
    puede_reactivar: bool
    criterio_aplicado: str
    es_calculo_hipotetico: bool  # NUEVO: indica si es cálculo hipotético

    def to_dict(self) -> Dict[str, Any]:
        resultado = {
            "ley_aplicable": self.ley_aplicable,
            "semanas_reconocidas": self.semanas_reconocidas,
            "años_cotizados": round(self.años_cotizados, 2),
            "conservacion_años": round(self.conservacion_años, 2),
            "conservacion_dias": self.conservacion_dias,
            "fecha_ultima_baja": self.fecha_ultima_baja.isoformat() if self.fecha_ultima_baja else None,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            
            # ✅ CAMBIO 1: true/false → Sí/No
            "esta_vigente": "Sí" if self.esta_vigente else "No",
            
            # ✅ CAMBIO 2: puede_reactivar con formato Sí/No
            "puede_reactivar": "Sí" if self.puede_reactivar else "No",
            
            # ✅ CAMBIO 3: Quitar criterio_aplicado del output
            # "criterio_aplicado": self.criterio_aplicado,
            
            "es_calculo_hipotetico": self.es_calculo_hipotetico
        }

        # Agregar leyendas si es cálculo hipotético
        if self.es_calculo_hipotetico:
            resultado["leyendas"] = [
                "⚠️ CÁLCULO ESTIMADO: Este trabajador aún está vigente en el IMSS",
                "📅 FECHA ESTIMADA: La fecha de vencimiento es una estimación basada en la fecha de emisión del reporte de semanas cotizadas",
                "🔄 ACTUALIZACIÓN RECOMENDADA: Consulte nuevamente cuando el trabajador cause baja definitiva"
            ]
            resultado["tipo_calculo"] = "HIPOTETICO_TRABAJADOR_VIGENTE"

        return resultado


class CalculadoraConservacionDerechos:
    """
    Calculadora de conservación de derechos IMSS según Ley 73 y Ley 97

    Reglas implementadas:
    - Ley 73: Conservación = floor(semanas_cotizadas/4) semanas desde última baja
    - Ley 97: Conservación = floor(años_cotizados) * 52 semanas desde última baja
    - Máximo en ambas leyes: 12 años
    - Reactivación: 52 semanas en período de 5 años
    - NUEVO: Cálculo hipotético para trabajadores vigentes usando fecha de emisión

    INTEGRACIÓN: Trabaja con datos ya corregidos por correccion_semanas_final.py
    """

    SEMANAS_POR_AÑO = 52
    MAXIMO_CONSERVACION_AÑOS = 12
    SEMANAS_REACTIVACION = 52
    PERIODO_REACTIVACION_AÑOS = 5

    def __init__(self):
        self.fecha_actual = datetime.now()

    def determinar_ley_aplicable(self, fecha_primer_alta: datetime) -> str:
        """
        Determina qué ley aplica basándose en la fecha de primer alta

        Args:
            fecha_primer_alta: Fecha del primer alta en el IMSS

        Returns:
            "Ley 73" si el primer alta fue antes del 1 julio 1997, "Ley 97" en caso contrario
        """
        fecha_cambio_ley = datetime(1997, 7, 1)
        return "Ley 73" if fecha_primer_alta < fecha_cambio_ley else "Ley 97"

    def calcular_conservacion_ley73_oficial(self, total_semanas_oficial: int) -> int:
        """
        Ley 73: Conservación = max(floor(semanas_reconocidas / 4), 52) semanas (máx. 12 años)
        CORREGIDO: Agrega mínimo legal de 52 semanas (1 año, Art. 150 LSS 73)
        """
        conservacion_semanas = total_semanas_oficial // 4  # floor division
        min_semanas = 52  # Mínimo legal: 1 año
        conservacion_semanas = max(conservacion_semanas, min_semanas)
        max_semanas = self.MAXIMO_CONSERVACION_AÑOS * 52   # 12 años en semanas
        return min(conservacion_semanas, max_semanas)

    def calcular_conservacion_ley97_oficial(self, total_semanas_oficial: int) -> int:
        """
        Ley 97: Conservación = min(años_cotizados * 52, 12 años * 52) semanas
        CORREGIDO: Retorna SEMANAS, no años
        """
        años_cotizados = total_semanas_oficial // 52       # años completos
        conservacion_semanas = años_cotizados * 52         # convertir a semanas
        max_semanas = self.MAXIMO_CONSERVACION_AÑOS * 52   # 12 años en semanas
        return min(conservacion_semanas, max_semanas)

    def esta_vigente_conservacion_oficial(self, fecha_ultima_baja: Optional[datetime],
                                        conservacion_semanas: int) -> bool:
        """
        Verifica vigencia usando semanas directas (método IMSS oficial)

        Args:
            fecha_ultima_baja: Fecha de la última baja
            conservacion_semanas: Semanas de conservación (no años)

        Returns:
            True si está vigente, False en caso contrario
        """
        if fecha_ultima_baja is None:
            return True  # Si no hay baja, está activo

        fecha_vencimiento = fecha_ultima_baja + timedelta(weeks=conservacion_semanas)
        return self.fecha_actual <= fecha_vencimiento

    def calcular_conservacion_derechos(self,
                                     datos_corregidos: Dict[str, Any],
                                     fecha_emision: Optional[str] = None) -> ResultadoConservacion:
        """
        Calcula conservación de derechos usando MÉTODO OFICIAL IMSS
        ACTUALIZADO: Usa nomenclatura oficial estandarizada y fechas hipotéticas

        - Ley 73: Conservación en SEMANAS = floor(total_semanas / 4)
        - Ley 97: Conservación en SEMANAS = floor(total_semanas / 52) * 52 (max 52*12)
        - Suma semanas directamente a fecha_ultima_baja
        - NUEVO: Para trabajadores vigentes, usa fecha de emisión como baja hipotética

        Args:
            datos_corregidos: Resultado del corrector (con empalmes eliminados)
            fecha_emision: Fecha de emisión del reporte

        Returns:
            ResultadoConservacion con cálculos exactos al IMSS oficial
        """
        try:
            # 1. OBTENER EL "TOTAL DE SEMANAS COTIZADAS" OFICIAL - NOMENCLATURA ACTUALIZADA
            datos_basicos = datos_corregidos.get('datos_basicos', {})

            # ✅ Priorizar nomenclatura oficial IMSS (actualizada)
            total_semanas_oficial = (
                datos_basicos.get('total_semanas_cotizadas', 0) or
                datos_basicos.get('semanas_cotizadas_imss', 0)
            )

            # ✅ Si no existe en datos_basicos, buscar en corrección aplicada
            if total_semanas_oficial == 0:
                correccion_info = datos_corregidos.get('correccion_aplicada', {})
                total_semanas_oficial = (
                    correccion_info.get('total_semanas_cotizadas', 0) or
                    correccion_info.get('semanas_cotizadas_imss_calculadas', 0)
                )

            if total_semanas_oficial == 0:
                raise ValueError("No se encontró total de semanas oficial del IMSS")

            # 2. PROCESAR PERÍODOS PARA ENCONTRAR FECHAS
            historial = datos_corregidos.get('historial_laboral', {})
            periodos_corregidos = historial.get('periodos', [])

            periodos_procesados = self._procesar_periodos_corregidos(
                periodos_corregidos,
                fecha_emision or datos_basicos.get('fecha_emision')
            )

            # 3. DETERMINAR LEY APLICABLE
            fecha_primer_alta = self._encontrar_primer_alta(periodos_procesados)
            if fecha_primer_alta is None:
                raise ValueError("No se pudo determinar la fecha de primer alta")

            ley = self.determinar_ley_aplicable(fecha_primer_alta)

            # 4. CALCULAR CONSERVACIÓN EN SEMANAS (MÉTODO OFICIAL)
            if ley == "Ley 73":
                # Ley 73: Una cuarta parte del tiempo cotizado
                conservacion_semanas = self.calcular_conservacion_ley73_oficial(total_semanas_oficial)
                criterio_base = f"Una cuarta parte del tiempo cotizado (máx. {self.MAXIMO_CONSERVACION_AÑOS} años)"
            else:
                # Ley 97: Todo el tiempo cotizado (max 12 años)
                conservacion_semanas = self.calcular_conservacion_ley97_oficial(total_semanas_oficial)
                criterio_base = f"Todo el tiempo cotizado (máx. {self.MAXIMO_CONSERVACION_AÑOS} años)"

            # 5. ENCONTRAR ÚLTIMA BAJA (MODIFICADO: puede usar fecha hipotética)
            fecha_ultima_baja, es_hipotetico = self._encontrar_ultima_baja_con_hipotetica(
                periodos_procesados,
                fecha_emision or datos_basicos.get('fecha_emision')
            )

            # 6. CALCULAR FECHA DE VENCIMIENTO (MÉTODO OFICIAL)
            fecha_vencimiento = None
            if fecha_ultima_baja:
                # SUMAR SEMANAS DIRECTAMENTE (método IMSS)
                fecha_vencimiento = fecha_ultima_baja + timedelta(weeks=conservacion_semanas)

            # 7. VERIFICAR VIGENCIA (MODIFICADO: considera cálculo hipotético)
            if es_hipotetico:
                # Para trabajadores vigentes, siempre están vigentes
                esta_vigente = True
                # ✅ CAMBIO: Para trabajadores vigentes, no aplica reactivación
                puede_reactivar = False
            else:
                esta_vigente = self.esta_vigente_conservacion_oficial(fecha_ultima_baja, conservacion_semanas)
                
                # ✅ CAMBIO: Lógica mejorada de puede_reactivar
                # Solo puede reactivar si NO está vigente
                if esta_vigente:
                    puede_reactivar = False  # Si está vigente, no necesita reactivar
                else:
                    # Si NO está vigente, verificar si puede reactivar comparando con fecha actual
                    if fecha_vencimiento and fecha_vencimiento < self.fecha_actual:
                        # Ya venció, verificar si puede reactivar con 52 semanas en últimos 5 años
                        puede_reactivar = self.puede_reactivar_derechos(periodos_procesados, fecha_ultima_baja)
                    else:
                        puede_reactivar = False

            # 8. AJUSTAR CRITERIO SI ES CÁLCULO HIPOTÉTICO
            if es_hipotetico:
                criterio = f"{criterio_base} - Cálculo hipotético (trabajador vigente)"
            else:
                criterio = criterio_base

            # 9. CONVERTIR A VALORES PARA RESPUESTA
            años_cotizados = total_semanas_oficial / 52.0
            conservacion_años = conservacion_semanas / 52.0
            conservacion_dias = int(conservacion_años * 365.25)

            return ResultadoConservacion(
                ley_aplicable=ley,
                semanas_reconocidas=total_semanas_oficial,
                años_cotizados=años_cotizados,
                conservacion_años=conservacion_años,
                conservacion_dias=conservacion_dias,
                fecha_ultima_baja=fecha_ultima_baja,
                fecha_vencimiento=fecha_vencimiento,
                esta_vigente=esta_vigente,
                puede_reactivar=puede_reactivar,
                criterio_aplicado=criterio,
                es_calculo_hipotetico=es_hipotetico
            )

        except Exception as e:
            raise ValueError(f"Error calculando conservación oficial: {str(e)}")

    def _procesar_periodos_corregidos(self, periodos_corregidos: List[Dict],
                                    fecha_emision: str) -> List[Dict]:
        """
        Convierte períodos corregidos al formato estándar para conservación

        Args:
            periodos_corregidos: Períodos ya procesados por correccion_semanas_final.py
            fecha_emision: Fecha de emisión del reporte

        Returns:
            Lista de períodos en formato estándar
        """
        periodos_procesados = []

        for periodo in periodos_corregidos:
            try:
                # Convertir fechas
                fecha_alta = self._convertir_fecha(periodo.get('fecha_inicio'))

                # Manejar fecha de baja (casos vigentes)
                fecha_fin = periodo.get('fecha_fin', '')
                if fecha_fin == 'Vigente' or not fecha_fin:
                    # Usar fecha de emisión como fecha de referencia para vigentes
                    fecha_baja = self._convertir_fecha(fecha_emision) if fecha_emision else None
                else:
                    fecha_baja = self._convertir_fecha(fecha_fin)

                periodo_procesado = {
                    'fecha_alta': fecha_alta,
                    'fecha_baja': fecha_baja,
                    'semanas': periodo.get('semanas_corregidas', periodo.get('semanas_cotizadas', 0)),
                    'salario': periodo.get('salario_diario', 0),
                    'patron': periodo.get('patron', ''),
                    'tipo_movimiento': periodo.get('tipo_movimiento', ''),
                    'es_vigente': fecha_fin == 'Vigente' or not fecha_fin
                }

                periodos_procesados.append(periodo_procesado)

            except Exception as e:
                print(f"Error procesando período: {e}")
                continue

        return periodos_procesados

    def _encontrar_ultima_baja_con_hipotetica(self, periodos_procesados: List[Dict],
                                           fecha_emision: str) -> tuple[Optional[datetime], bool]:
        """
        MODIFICADO: Encuentra la última baja o usa fecha de emisión como baja hipotética
        para trabajadores vigentes

        Args:
            periodos_procesados: Períodos ya procesados
            fecha_emision: Fecha de emisión del reporte

        Returns:
            Tupla con (fecha_baja, es_hipotetico)
        """
        ultima_baja = None
        hay_vigente = False

        for periodo in periodos_procesados:
            # Si hay al menos un período vigente
            if periodo.get('es_vigente', False):
                hay_vigente = True
                continue

            fecha_baja = periodo.get('fecha_baja')
            if fecha_baja and isinstance(fecha_baja, datetime):
                if ultima_baja is None or fecha_baja > ultima_baja:
                    ultima_baja = fecha_baja

        # MODIFICACIÓN: Si hay períodos vigentes, usar fecha de emisión como baja hipotética
        if hay_vigente and fecha_emision:
            try:
                fecha_hipotetica = self._convertir_fecha(fecha_emision)
                if fecha_hipotetica:
                    return fecha_hipotetica, True  # Es cálculo hipotético
            except:
                pass

        # Si hay vigentes pero no se pudo parsear fecha de emisión, usar fecha actual
        if hay_vigente:
            return self.fecha_actual, True  # Es cálculo hipotético

        return ultima_baja, False  # No es hipotético

    def _convertir_fecha(self, fecha_str: str) -> Optional[datetime]:
        """
        Convierte string de fecha en datetime
        Compatible con formatos de correccion_semanas_final.py

        Args:
            fecha_str: Fecha como string

        Returns:
            datetime object o None si no se puede convertir
        """
        if not fecha_str or fecha_str == "Vigente":
            return None

        # Formatos usados en correccion_semanas_final.py
        formatos = [
            "%d/%m/%Y",      # Formato principal usado en corrección
            "%Y-%m-%d",      # Formato de fecha_emision
            "%d-%m-%Y",
            "%d/%m/%y",
            "%d-%m-%y"
        ]

        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato)
            except ValueError:
                continue

        return None

    def _encontrar_primer_alta(self, periodos_procesados: List[Dict]) -> Optional[datetime]:
        """
        Encuentra la fecha del primer alta en el historial

        Args:
            periodos_procesados: Lista de períodos procesados

        Returns:
            Fecha del primer alta o None si no se encuentra
        """
        primer_alta = None

        for periodo in periodos_procesados:
            fecha_alta = periodo.get('fecha_alta')
            if fecha_alta and isinstance(fecha_alta, datetime):
                if primer_alta is None or fecha_alta < primer_alta:
                    primer_alta = fecha_alta

        return primer_alta

    def puede_reactivar_derechos(self, periodos_procesados: List[Dict],
                                fecha_ultima_baja: Optional[datetime]) -> bool:
        """
        Verifica si puede reactivar derechos con 52 semanas en 5 años

        Args:
            periodos_procesados: Lista de períodos procesados
            fecha_ultima_baja: Fecha de la última baja

        Returns:
            True si puede reactivar, False en caso contrario
        """
        if fecha_ultima_baja is None:
            return False  # Si está activo, no necesita reactivación

        # Buscar períodos después de la última baja en los últimos 5 años
        fecha_limite = self.fecha_actual - timedelta(days=self.PERIODO_REACTIVACION_AÑOS * 365.25)
        fecha_inicio_busqueda = max(fecha_ultima_baja, fecha_limite)

        semanas_posteriores = 0
        for periodo in periodos_procesados:
            fecha_alta = periodo.get('fecha_alta')
            fecha_baja = periodo.get('fecha_baja')

            if not fecha_alta:
                continue

            # Si el alta es posterior a la última baja y dentro de los 5 años
            if fecha_alta > fecha_inicio_busqueda:
                fecha_fin_periodo = fecha_baja if fecha_baja else self.fecha_actual
                if fecha_fin_periodo > fecha_alta:
                    dias_periodo = (fecha_fin_periodo - fecha_alta).days
                    semanas_periodo = dias_periodo / 7
                    semanas_posteriores += semanas_periodo

        return semanas_posteriores >= self.SEMANAS_REACTIVACION

# Función de ejemplo para testing
def ejemplo_uso_con_datos_corregidos():
    """Ejemplo de uso integrado con correccion_semanas_final.py - ACTUALIZADO CON FECHAS HIPOTÉTICAS"""

    # Simular datos ya corregidos por correccion_semanas_final.py - NOMENCLATURA OFICIAL
    datos_corregidos = {
        'datos_basicos': {
            'fecha_emision': '2025-01-29',  # Fecha de emisión del reporte
            'semanas_cotizadas_imss': 1882,          # ✅ Término oficial
            'semanas_descontadas': 0,                 # ✅ Término oficial
            'semanas_reintegradas': 0,                # ✅ Término oficial
            'total_semanas_cotizadas': 1882           # ✅ Término oficial
        },
        'correccion_aplicada': {
            'total_semanas_cotizadas': 1881,          # ✅ Ya sin empalmes
            'semanas_cotizadas_imss_calculadas': 1881, # ✅ Calculado exacto
            'es_exacto': True,
            'empalmes_corregidos': 0
        },
        'historial_laboral': {
            'periodos': [
                {
                    'fecha_inicio': '09/03/1989',
                    'fecha_fin': 'Vigente',  # Trabajador vigente
                    'semanas_corregidas': 1881,
                    'patron': 'BIMBO',
                    'salario_diario': 925.35
                },
                {
                    'fecha_inicio': '17/06/1986',
                    'fecha_fin': '16/08/1986',
                    'semanas_corregidas': 8,
                    'patron': 'EMPRESA ANTERIOR',
                    'salario_diario': 50.0
                }
            ]
        }
    }

    # Calcular conservación
    calculadora = CalculadoraConservacionDerechos()
    resultado = calculadora.calcular_conservacion_derechos(
        datos_corregidos=datos_corregidos,
        fecha_emision='2025-01-29'
    )

    print("=== CONSERVACIÓN DE DERECHOS IMSS CON FECHAS HIPOTÉTICAS ===")
    print(f"Ley aplicable: {resultado.ley_aplicable}")
    print(f"Total semanas cotizadas: {resultado.semanas_reconocidas}")
    print(f"Conservación: {resultado.conservacion_años:.2f} años ({resultado.conservacion_dias} días)")
    print(f"Fecha última baja: {resultado.fecha_ultima_baja.strftime('%d/%m/%Y') if resultado.fecha_ultima_baja else 'N/A'}")
    print(f"Fecha vencimiento: {resultado.fecha_vencimiento.strftime('%d/%m/%Y') if resultado.fecha_vencimiento else 'N/A'}")
    print(f"Estado: {'VIGENTE' if resultado.esta_vigente else 'VENCIDO'}")
    print(f"Es cálculo hipotético: {'SÍ' if resultado.es_calculo_hipotetico else 'NO'}")
    print(f"Criterio: {resultado.criterio_aplicado}")
    print("✅ Usando fechas hipotéticas para trabajadores vigentes")

    return resultado.to_dict()


if __name__ == "__main__":
    ejemplo_uso_con_datos_corregidos()


