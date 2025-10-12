"""
Módulo para calcular el salario promedio de las últimas 250 semanas cotizadas
Implementa las reglas oficiales del IMSS según Art. 167 Ley 73

COORDINA CON: correccion_semanas_final.py
USO: from calculo_250_semanas import Calculadora250Semanas
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class SegmentoSalarial:
    """Representa un segmento de salario homogéneo"""
    fecha_inicio: datetime
    fecha_fin: datetime
    salario_diario: float
    salario_diario_ajustado: float
    dias_efectivos: int
    patron: str
    registro_patronal: str

@dataclass
class ResultadoPromedio250:
    """Resultado del cálculo de promedio 250 semanas"""
    salario_promedio_diario: float
    salario_promedio_mensual: float
    total_dias_calculados: int
    total_segmentos: int
    fecha_inicio_ventana: datetime
    fecha_fin_ventana: datetime
    segmentos_utilizados: List[SegmentoSalarial]
    suma_ponderada: float
    tiene_250_semanas_completas: bool
    observaciones: List[str]

    def _formatear_segmentos_simple(self) -> List[str]:
        """
        ✅ NUEVO: Formato simple y visual como en debug
        Ejemplo: "BENTELER DE MEXICO: $189.13 × 14 días"
        """
        segmentos_formateados = []
        
        for i, seg in enumerate(self.segmentos_utilizados, 1):
            linea = f"{i}. {seg.patron}: ${seg.salario_diario_ajustado:.2f} × {seg.dias_efectivos} días"
            segmentos_formateados.append(linea)
        
        return segmentos_formateados

    def to_dict(self) -> Dict[str, Any]:
        return {
            "salario_promedio_diario": round(self.salario_promedio_diario, 2),
            "salario_promedio_mensual": round(self.salario_promedio_mensual, 2),
            "total_dias_calculados": self.total_dias_calculados,
            
            # ✅ CAMBIO: total_segmentos oculto (comentado)
            # "total_segmentos": self.total_segmentos,
            
            "fecha_inicio_ventana": self.fecha_inicio_ventana.isoformat() if self.fecha_inicio_ventana else None,
            "fecha_fin_ventana": self.fecha_fin_ventana.isoformat() if self.fecha_fin_ventana else None,
            "suma_ponderada": round(self.suma_ponderada, 2),
            
            # ✅ CAMBIO: true/false → Sí/No
            "tiene_250_semanas_completas": "Sí" if self.tiene_250_semanas_completas else "No",
            
            # ✅ CAMBIO: Usar nuevo formato simple de segmentos
            "segmentos_utilizados": self._formatear_segmentos_simple(),
            
            "observaciones": self.observaciones,
            
            # NUEVO: Detalle del cálculo
            "detalle_calculo": {
                "salario_minimo": round(min([s.salario_diario_ajustado for s in self.segmentos_utilizados]), 2) if self.segmentos_utilizados else 0,
                "salario_maximo": round(max([s.salario_diario_ajustado for s in self.segmentos_utilizados]), 2) if self.segmentos_utilizados else 0,
                "cambios_salariales_detectados": len(self.segmentos_utilizados) - 1 if len(self.segmentos_utilizados) > 1 else 0
            }
        }

class Calculadora250Semanas:
    """
    Calculadora del salario promedio de las últimas 250 semanas cotizadas
    según reglas oficiales IMSS Art. 167 Ley 73
    """

    # Constantes oficiales IMSS
    SEMANAS_PARA_PROMEDIO = 250
    DIAS_PARA_PROMEDIO = 1750

    # Topes históricos (VSM - Veces Salario Mínimo)
    TOPES_HISTORICOS = {
        ("1900-01-01", "1997-06-30"): 10,
        ("1997-07-01", "2007-06-30"): 20,
        ("2007-07-01", "2025-12-31"): 25,
    }

    def __init__(self, modo_debug: bool = False):
        self.modo_debug = modo_debug
        self.salarios_minimos = self._cargar_salarios_minimos_historicos()

    def calcular_promedio_250_semanas(self, datos_corregidos: Dict[str, Any],
                                    fecha_referencia: Optional[str] = None) -> ResultadoPromedio250:
        """
        Calcula el promedio salarial de las últimas 250 semanas cotizadas
        """
        try:
            # 1. Obtener períodos ya corregidos
            periodos = self._extraer_periodos_corregidos(datos_corregidos)

            # 2. Determinar fecha de referencia
            fecha_ref = self._determinar_fecha_referencia(periodos, fecha_referencia, datos_corregidos)

            # 3. Crear segmentos salariales detallados
            segmentos = self._crear_segmentos_salariales(periodos)

            # 4. Filtrar últimas 250 semanas
            segmentos_filtrados = self._filtrar_ultimas_250_semanas(segmentos, fecha_ref)

            # 5. Aplicar topes históricos
            segmentos_con_topes = self._aplicar_topes_historicos(segmentos_filtrados)

            # 6. Calcular promedio ponderado
            resultado = self._calcular_promedio_ponderado(segmentos_con_topes, fecha_ref)

            if self.modo_debug:
                self._imprimir_debug(resultado)

            return resultado

        except Exception as e:
            if self.modo_debug:
                print(f"Error en cálculo 250 semanas: {e}")
            return self._crear_resultado_error(str(e))

    def _extraer_periodos_corregidos(self, datos_corregidos: Dict[str, Any]) -> List[Dict]:
        """Extrae períodos ya corregidos del resultado del parser"""
        historial = datos_corregidos.get('historial_laboral', {})
        periodos = historial.get('periodos', [])

        if not periodos:
            raise ValueError("No se encontraron períodos en historial_laboral")

        # ✅ Verificar que existe el campo 'semanas_corregidas' (puede ser 0)
        tiene_correccion = any('semanas_corregidas' in periodo for periodo in periodos)
        if not tiene_correccion:
            raise ValueError("Los datos deben provenir de correccion_semanas_final.py")

        return periodos

    def _determinar_fecha_referencia(self, periodos: List[Dict], fecha_referencia: Optional[str],
                                   datos_corregidos: Dict) -> datetime:
        """Determina la fecha desde la cual contar las 250 semanas hacia atrás"""
        if fecha_referencia:
            try:
                return datetime.strptime(fecha_referencia, '%Y-%m-%d')
            except:
                pass

        # Buscar última fecha de baja
        fechas_baja = []
        for periodo in periodos:
            if periodo.get('fecha_fin', '').lower() != 'vigente':
                try:
                    fecha_baja = datetime.strptime(periodo['fecha_fin'], '%d/%m/%Y')
                    fechas_baja.append(fecha_baja)
                except:
                    continue

        if fechas_baja:
            return max(fechas_baja)

        # Fallback: usar fecha de emisión
        fecha_emision = datos_corregidos.get('datos_basicos', {}).get('fecha_emision')
        if fecha_emision:
            try:
                return datetime.strptime(fecha_emision, '%Y-%m-%d')
            except:
                pass

        return datetime.now()

    def _crear_segmentos_salariales(self, periodos: List[Dict]) -> List[SegmentoSalarial]:
        """Crea segmentos salariales detallados considerando cambios de salario"""
        segmentos = []

        for periodo in periodos:
            try:
                fecha_inicio = datetime.strptime(periodo['fecha_inicio'], '%d/%m/%Y')

                if periodo.get('fecha_fin', '').lower() == 'vigente':
                    fecha_fin = datetime.now()
                else:
                    fecha_fin = datetime.strptime(periodo['fecha_fin'], '%d/%m/%Y')

                cambios_salario = periodo.get('cambios_salario', [])
                salario_base = periodo.get('salario_diario', 0)

                if not cambios_salario:
                    dias = (fecha_fin - fecha_inicio).days + 1
                    segmento = SegmentoSalarial(
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        salario_diario=salario_base,
                        salario_diario_ajustado=salario_base,
                        dias_efectivos=dias,
                        patron=periodo.get('patron', ''),
                        registro_patronal=periodo.get('registro_patronal', '')
                    )
                    segmentos.append(segmento)
                else:
                    segmentos_periodo = self._procesar_cambios_salario(
                        fecha_inicio, fecha_fin, cambios_salario, salario_base,
                        periodo.get('patron', ''), periodo.get('registro_patronal', '')
                    )
                    segmentos.extend(segmentos_periodo)

            except Exception as e:
                if self.modo_debug:
                    print(f"Error procesando período {periodo.get('patron', 'N/A')}: {e}")
                continue

        return segmentos

    def _procesar_cambios_salario(self, fecha_inicio: datetime, fecha_fin: datetime,
                                cambios: List[Dict], salario_base: float,
                                patron: str, registro: str) -> List[SegmentoSalarial]:
        """Procesa cambios de salario dentro de un período"""
        segmentos = []

        cambios_ordenados = sorted(cambios, key=lambda x: datetime.strptime(x['fecha'], '%d/%m/%Y'))

        fecha_actual = fecha_inicio
        salario_actual = salario_base

        for cambio in cambios_ordenados:
            try:
                fecha_cambio = datetime.strptime(cambio['fecha'], '%d/%m/%Y')

                if fecha_cambio > fecha_actual:
                    dias = (fecha_cambio - fecha_actual).days
                    if dias > 0:
                        segmento = SegmentoSalarial(
                            fecha_inicio=fecha_actual,
                            fecha_fin=fecha_cambio - timedelta(days=1),
                            salario_diario=salario_actual,
                            salario_diario_ajustado=salario_actual,
                            dias_efectivos=dias,
                            patron=patron,
                            registro_patronal=registro
                        )
                        segmentos.append(segmento)

                fecha_actual = fecha_cambio
                salario_actual = cambio.get('salario_diario', salario_actual)

            except Exception as e:
                if self.modo_debug:
                    print(f"Error procesando cambio de salario: {e}")
                continue

        if fecha_actual <= fecha_fin:
            dias = (fecha_fin - fecha_actual).days + 1
            if dias > 0:
                segmento = SegmentoSalarial(
                    fecha_inicio=fecha_actual,
                    fecha_fin=fecha_fin,
                    salario_diario=salario_actual,
                    salario_diario_ajustado=salario_actual,
                    dias_efectivos=dias,
                    patron=patron,
                    registro_patronal=registro
                )
                segmentos.append(segmento)

        return segmentos

    def _filtrar_ultimas_250_semanas(self, segmentos: List[SegmentoSalarial], fecha_ref: datetime) -> List[SegmentoSalarial]:
        """Filtra últimas 250 semanas cotizadas - FINAL FIX: Acumula cotizados secuenciales (salta gaps) hasta 1750 días"""
        if not segmentos:
            return []

        # Ordena por fecha_fin DESC (más recientes primero)
        segmentos_ordenados = sorted(segmentos, key=lambda s: s.fecha_fin, reverse=True)

        dias_acumulados = 0
        segmentos_filtrados = []

        for seg in segmentos_ordenados:
            if dias_acumulados >= self.DIAS_PARA_PROMEDIO:
                break

            # Usa días completos del seg (no clip calendario, acumula cotizados)
            dias_seg = seg.dias_efectivos
            dias_ventana = min(dias_seg, self.DIAS_PARA_PROMEDIO - dias_acumulados)

            if dias_ventana > 0:
                # Sub-segmento (todo o parte)
                sub_seg = SegmentoSalarial(
                    fecha_inicio=seg.fecha_inicio,
                    fecha_fin=seg.fecha_fin,
                    salario_diario=seg.salario_diario,
                    salario_diario_ajustado=seg.salario_diario_ajustado,
                    dias_efectivos=dias_ventana,
                    patron=seg.patron,
                    registro_patronal=seg.registro_patronal
                )
                segmentos_filtrados.append(sub_seg)
                dias_acumulados += dias_ventana

        # Ordena finales ASC para output
        segmentos_filtrados.sort(key=lambda s: s.fecha_inicio)

        if self.modo_debug:
            print(f"[DEBUG FILTRO] Acumulados cotizados: {dias_acumulados} días (de 1750), Segmentos: {len(segmentos_filtrados)}")
            print(f"[DEBUG FILTRO] Período extendido: {min(s.fecha_inicio for s in segmentos_filtrados).strftime('%Y-%m')} a {max(s.fecha_fin for s in segmentos_filtrados).strftime('%Y-%m')}")
            for s in segmentos_filtrados[:5]:
                print(f"  - {s.patron[:30]}: ${s.salario_diario:.2f} x {s.dias_efectivos} días ({s.fecha_inicio.strftime('%Y-%m')}-{s.fecha_fin.strftime('%Y-%m')})")

        return segmentos_filtrados

    def _aplicar_topes_historicos(self, segmentos_filtrados: List[SegmentoSalarial]) -> List[SegmentoSalarial]:
        """Aplica topes VSM históricos a cada segmento"""
        for seg in segmentos_filtrados:
            self._aplicar_tope_segmento(seg)
        return segmentos_filtrados

    def _obtener_tope_fecha(self, fecha: datetime) -> float:
        """Obtiene el tope de VSM aplicable"""
        fecha_str = fecha.strftime('%Y-%m-%d')

        for (inicio, fin), tope in self.TOPES_HISTORICOS.items():
            if inicio <= fecha_str <= fin:
                return tope

        return 25

    def _aplicar_tope_segmento(self, seg: SegmentoSalarial) -> float:
        """Aplica tope real: SBC_ajustado = min(SBC, VSM * SMG en fecha_inicio)"""
        smg = self._obtener_salario_minimo(seg.fecha_inicio)
        vsm = self._obtener_tope_fecha(seg.fecha_inicio)
        tope = vsm * smg
        seg.salario_diario_ajustado = min(seg.salario_diario, tope)
        return seg.salario_diario_ajustado

    def _calcular_promedio_ponderado(self, segmentos: List[SegmentoSalarial],
                               fecha_referencia: datetime) -> ResultadoPromedio250:
        """
        Calcula el promedio ponderado según la fórmula oficial IMSS:
        Promedio = Σ(SBC_ajustado × días_segmento) / días_disponibles

        Si hay menos de 250 semanas, calcula con las disponibles
        """
        suma_ponderada = 0.0
        total_dias = 0
        observaciones = []

        for segmento in segmentos:
            contribucion = segmento.salario_diario_ajustado * segmento.dias_efectivos
            suma_ponderada += contribucion
            total_dias += segmento.dias_efectivos

        # ✅ Calcular con los días disponibles (no forzar 1,750)
        if total_dias > 0:
            salario_promedio_diario = suma_ponderada / total_dias
        else:
            salario_promedio_diario = 0.0
            observaciones.append("No se encontraron períodos válidos para el cálculo")

        salario_promedio_mensual = salario_promedio_diario * 30.4

        # Determinar fechas de la ventana
        fecha_inicio_ventana = None
        fecha_fin_ventana = None
        if segmentos:
            fecha_inicio_ventana = min(s.fecha_inicio for s in segmentos)
            fecha_fin_ventana = max(s.fecha_fin for s in segmentos)

        # ✅ Validaciones mejoradas
        tiene_250_completas = total_dias >= self.DIAS_PARA_PROMEDIO

        if not tiene_250_completas and total_dias > 0:
            semanas_disponibles = total_dias // 7
            observaciones.append(
                f"⚠️ CÁLCULO PARCIAL: Solo se encontraron {semanas_disponibles} semanas "
                f"({total_dias} días) de las 250 requeridas (1,750 días)"
            )
            observaciones.append(
                f"El promedio se calculó sobre {semanas_disponibles} semanas disponibles"
            )
        elif tiene_250_completas and total_dias > self.DIAS_PARA_PROMEDIO:
            observaciones.append(
                f"✓ Cálculo completo con las últimas 250 semanas (1,750 días)"
            )

        if len(segmentos) == 0:
            observaciones.append("No se encontraron segmentos válidos")

        return ResultadoPromedio250(
            salario_promedio_diario=salario_promedio_diario,
            salario_promedio_mensual=salario_promedio_mensual,
            total_dias_calculados=total_dias,
            total_segmentos=len(segmentos),
            fecha_inicio_ventana=fecha_inicio_ventana,
            fecha_fin_ventana=fecha_fin_ventana,
            segmentos_utilizados=segmentos,
            suma_ponderada=suma_ponderada,
            tiene_250_semanas_completas=tiene_250_completas,
            observaciones=observaciones
        )

    def _cargar_salarios_minimos_historicos(self) -> Dict[str, float]:
        """Carga tabla histórica completa de SMG general (resto del país) - Fuente: CONASAMI/INEGI"""
        return {
            "1987": 3.05, "1988": 7.77, "1989": 8.64, "1990": 11.90,
            "1991": 13.33, "1992": 13.33, "1993": 14.27, "1994": 15.27,
            "1995": 16.34, "1996": 22.60, "1997": 26.45, "1998": 30.20,
            "1999": 34.45, "2000": 37.90, "2001": 40.35, "2002": 42.15,
            "2003": 43.65, "2004": 45.24, "2005": 46.80, "2006": 48.67,
            "2007": 50.57, "2008": 52.59, "2009": 54.80, "2010": 57.46,
            "2011": 59.82, "2012": 62.33, "2013": 64.76, "2014": 67.29,
            "2015": 70.10, "2016": 73.04, "2017": 80.04, "2018": 88.36,
            "2019": 102.68, "2020": 123.22, "2021": 141.70, "2022": 172.87,
            "2023": 207.44, "2024": 248.93, "2025": 278.80
        }

    def _obtener_salario_minimo(self, fecha: datetime) -> float:
        """Obtiene el salario mínimo vigente en la fecha - CORREGIDO: Fallback al año histórico mínimo"""
        año = str(fecha.year)

        if año in self.salarios_minimos:
            if self.modo_debug:
                print(f"[DEBUG SMG] Año {año}: ${self.salarios_minimos[año]:.2f}")
            return self.salarios_minimos[año]

        años_disponibles = sorted([int(a) for a in self.salarios_minimos.keys()])
        año_int = fecha.year

        for año_hist in reversed(años_disponibles):
            if año_hist <= año_int:
                if self.modo_debug:
                    print(f"[DEBUG SMG] Año {año} no encontrado, usando {año_hist}: ${self.salarios_minimos[str(año_hist)]:.2f}")
                return self.salarios_minimos[str(año_hist)]

        # Fallback corregido: Usa el año más antiguo de la tabla (no fijo en 1990)
        año_minimo = min(años_disponibles)
        if self.modo_debug:
            print(f"[DEBUG SMG] Fallback extremo a año mínimo {año_minimo}: ${self.salarios_minimos[str(año_minimo)]:.2f}")
        return self.salarios_minimos[str(año_minimo)]

    def _imprimir_debug(self, resultado: ResultadoPromedio250):
        """Imprime información de debug"""
        print("=== DEBUG CÁLCULO 250 SEMANAS ===")
        print(f"Salario promedio diario: ${resultado.salario_promedio_diario:.2f}")
        print(f"Salario promedio mensual: ${resultado.salario_promedio_mensual:.2f}")
        print(f"Días calculados: {resultado.total_dias_calculados} / 1,750")
        print(f"Segmentos procesados: {resultado.total_segmentos}")
        print(f"Período: {resultado.fecha_inicio_ventana} - {resultado.fecha_fin_ventana}")
        print(f"Suma ponderada: ${resultado.suma_ponderada:.2f}")
        print(f"250 semanas completas: {resultado.tiene_250_semanas_completas}")

        if resultado.observaciones:
            print("Observaciones:")
            for obs in resultado.observaciones:
                print(f"  - {obs}")

        print("Detalle por segmento:")
        for i, seg in enumerate(resultado.segmentos_utilizados[:10]):
            print(f"  {i+1}. {seg.patron[:30]}: ${seg.salario_diario_ajustado:.2f} × {seg.dias_efectivos} días")
        print("=== FIN DEBUG ===")

    def _crear_resultado_error(self, error: str) -> ResultadoPromedio250:
        """Crea resultado de error"""
        return ResultadoPromedio250(
            salario_promedio_diario=0.0,
            salario_promedio_mensual=0.0,
            total_dias_calculados=0,
            total_segmentos=0,
            fecha_inicio_ventana=None,
            fecha_fin_ventana=None,
            segmentos_utilizados=[],
            suma_ponderada=0.0,
            tiene_250_semanas_completas=False,
            observaciones=[f"Error en cálculo: {error}"]
        )


def calcular_promedio_250_desde_correccion(datos_corregidos: Dict[str, Any],
                                         fecha_referencia: Optional[str] = None,
                                         debug: bool = False) -> Dict[str, Any]:
    """Función principal para integración con el pipeline"""
    calculadora = Calculadora250Semanas(modo_debug=debug)
    resultado = calculadora.calcular_promedio_250_semanas(datos_corregidos, fecha_referencia)
    return resultado.to_dict()


if __name__ == "__main__":
    pass


