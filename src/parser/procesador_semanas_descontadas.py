"""
Procesador de semanas descontadas y reintegradas según reglas IMSS
Maneja el impacto de semanas descontadas en conservación de derechos

COORDINA CON: correccion_semanas_final.py y conservacion_derechos.py
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalisisSemanas:
    """Resultado del análisis de semanas - NOMENCLATURA OFICIAL IMSS"""
    semanas_cotizadas_imss: int              # "Semanas cotizadas IMSS"
    semanas_descontadas: int                  # "Semanas Descontadas"
    semanas_reintegradas: int                 # "Semanas Reintegradas"
    total_semanas_cotizadas: int              # "Total de semanas cotizadas"
    porcentaje_descuento: float
    impacto_conservacion: str
    observaciones: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "semanas_cotizadas_imss": self.semanas_cotizadas_imss,
            "semanas_descontadas": self.semanas_descontadas,
            "semanas_reintegradas": self.semanas_reintegradas,
            "total_semanas_cotizadas": self.total_semanas_cotizadas,
            "porcentaje_descuento": round(self.porcentaje_descuento, 2),
            # ✅ CAMBIO: Quitar impacto_conservacion del output
            # "impacto_conservacion": self.impacto_conservacion,
            "observaciones": self.observaciones
        }


class ProcesadorSemanasDescontadas:
    """
    Procesador que maneja semanas descontadas según reglas IMSS:

    NOMENCLATURA OFICIAL IMSS:
    - Semanas cotizadas IMSS = Total bruto registrado
    - Semanas Descontadas = SOLO por disposición de recursos AFORE
    - Total de semanas cotizadas = Semanas IMSS - Semanas Descontadas + Reintegradas

    IMPORTANTE: Los empalmes NO son descuentos, son correcciones de fechas
    """

    def procesar_semanas_desde_correccion(self, datos_corregidos: Dict[str, Any]) -> AnalisisSemanas:
        """
        Procesa semanas usando datos ya corregidos por correccion_semanas_final.py
        CORREGIDO: Usa nomenclatura oficial IMSS y lógica correcta

        Args:
            datos_corregidos: Datos procesados con corrección de empalmes

        Returns:
            AnalisisSemanas con el análisis completo
        """
        try:
            # Obtener datos básicos
            datos_basicos = datos_corregidos.get('datos_basicos', {})
            correccion_info = datos_corregidos.get('correccion_aplicada', {})

            # ✅ NOMENCLATURA OFICIAL IMSS
            # 1. Semanas cotizadas IMSS (bruto)
            semanas_cotizadas_imss = (
                datos_basicos.get('semanas_cotizadas_imss', 0) or
                datos_basicos.get('total_semanas_cotizadas', 0)
            )

            # 2. Semanas descontadas (SOLO disposición recursos AFORE)
            semanas_descontadas = self._extraer_semanas_descontadas(datos_basicos)

            # 3. Semanas reintegradas
            semanas_reintegradas = self._extraer_semanas_reintegradas(datos_basicos)

            # 4. Total de semanas cotizadas - DEBE SER DEL PDF OFICIAL
            # ✅ CORRECCIÓN CRÍTICA: SIEMPRE usar datos_basicos primero
            total_semanas_cotizadas = datos_basicos.get('total_semanas_cotizadas', 0)

            # Si no viene en datos_basicos, calcular con la fórmula oficial
            if not total_semanas_cotizadas or total_semanas_cotizadas == 0:
                total_semanas_cotizadas = (
                    semanas_cotizadas_imss - semanas_descontadas + semanas_reintegradas
                )
                logger.warning(
                    f"⚠️ Total no encontrado en PDF, calculado: "
                    f"{semanas_cotizadas_imss} - {semanas_descontadas} + {semanas_reintegradas} = {total_semanas_cotizadas}"
                )

            # Las semanas reconocidas para conservación = Total semanas cotizadas
            semanas_reconocidas = total_semanas_cotizadas

            # Calcular porcentaje de descuento (sobre el bruto IMSS)
            porcentaje_descuento = 0
            if semanas_cotizadas_imss > 0:
                porcentaje_descuento = (semanas_descontadas / semanas_cotizadas_imss) * 100

            # Determinar impacto en conservación
            impacto = self._determinar_impacto_conservacion(porcentaje_descuento, semanas_descontadas)

            # Generar observaciones corregidas
            observaciones = self._generar_observaciones_integradas(
                semanas_reconocidas,  # ✅ CORREGIDO: usar semanas_reconocidas
                semanas_descontadas,
                semanas_reintegradas,
                correccion_info,
                porcentaje_descuento
            )

            return AnalisisSemanas(
                semanas_cotizadas_imss=semanas_cotizadas_imss,
                semanas_descontadas=semanas_descontadas,
                semanas_reintegradas=semanas_reintegradas,
                total_semanas_cotizadas=total_semanas_cotizadas,
                porcentaje_descuento=porcentaje_descuento,
                impacto_conservacion=impacto,
                observaciones=observaciones
            )

        except Exception as e:
            return self._crear_analisis_error(str(e))

    def _extraer_semanas_descontadas(self, datos_basicos: Dict[str, Any]) -> int:
        """
        Extrae semanas descontadas de datos básicos
        SOLO por disposición de recursos AFORE (no empalmes)
        """
        # Buscar en campos conocidos
        campos_descuento = [
            'semanas_descontadas',
            'descuentos_semanas',
            'semanas_no_reconocidas',
            'ajustes_negativos'
        ]

        for campo in campos_descuento:
            valor = datos_basicos.get(campo, 0)
            if valor and isinstance(valor, (int, float)):
                return int(valor)

        return 0

    def _extraer_semanas_reintegradas(self, datos_basicos: Dict[str, Any]) -> int:
        """Extrae semanas reintegradas de datos básicos"""
        campos_reintegro = [
            'semanas_reintegradas',
            'reintegros_semanas',
            'semanas_recuperadas',
            'ajustes_positivos'
        ]

        for campo in campos_reintegro:
            valor = datos_basicos.get(campo, 0)
            if valor and isinstance(valor, (int, float)):
                return int(valor)

        return 0

    def _determinar_impacto_conservacion(self, porcentaje_descuento: float, semanas_descontadas: int) -> str:
        """Determina el impacto de los descuentos en conservación"""
        if semanas_descontadas == 0:
            return "SIN_IMPACTO"
        elif porcentaje_descuento < 5:
            return "IMPACTO_MENOR"
        elif porcentaje_descuento < 15:
            return "IMPACTO_MODERADO"
        elif porcentaje_descuento < 30:
            return "IMPACTO_SIGNIFICATIVO"
        else:
            return "IMPACTO_SEVERO"

    def _generar_observaciones_integradas(self, semanas_reconocidas: int, semanas_descontadas: int,
                                        semanas_reintegradas: int, correccion_info: Dict,
                                        porcentaje_descuento: float) -> List[str]:
        """
        Genera observaciones integradas con corrección de empalmes
        ✅ CORREGIDO: Usa semanas_reconocidas correctamente
        """
        observaciones = []

        # Información de corrección de empalmes (NO son descuentos)
        empalmes_corregidos = correccion_info.get('empalmes_corregidos', 0)
        mejora_semanas = correccion_info.get('mejora_semanas', 0)

        if empalmes_corregidos > 0:
            observaciones.append(f"Se corrigieron {empalmes_corregidos} empalmes, reduciendo {mejora_semanas} semanas")

        # Información de descuentos (SOLO disposición recursos)
        if semanas_descontadas > 0:
            observaciones.append(f"IMSS descontó {semanas_descontadas} semanas ({porcentaje_descuento:.1f}% del total)")

            if porcentaje_descuento > 15:
                observaciones.append("⚠️ Alto porcentaje de descuento - revisar causas con IMSS")

        # Información de reintegros
        if semanas_reintegradas > 0:
            observaciones.append(f"Se reintegraron {semanas_reintegradas} semanas al total reconocido")

        # ✅ CORRECCIÓN CRÍTICA: Usar semanas_reconocidas
        observaciones.append(f"Total reconocido para conservación: {semanas_reconocidas} semanas")

        # Precisión de la corrección
        if correccion_info.get('es_exacto'):
            observaciones.append("Precisión exacta respecto al IMSS")
        else:
            precision = correccion_info.get('precision_final', 0)
            observaciones.append(f"Precisión: ±{precision} semanas respecto al IMSS")

        return observaciones

    def _crear_analisis_error(self, error: str) -> AnalisisSemanas:
        """Crea análisis de error cuando falla el procesamiento"""
        return AnalisisSemanas(
            semanas_cotizadas_imss=0,
            semanas_descontadas=0,
            semanas_reintegradas=0,
            total_semanas_cotizadas=0,
            porcentaje_descuento=0,
            impacto_conservacion="ERROR",
            observaciones=[f"Error procesando semanas: {error}"]
        )

    def generar_reporte_impacto(self, analisis: AnalisisSemanas, conservacion_años: float) -> Dict[str, Any]:
        """
        Genera reporte del impacto de descuentos en conservación de derechos

        Args:
            analisis: Resultado del análisis de semanas
            conservacion_años: Años de conservación calculados

        Returns:
            Reporte completo de impacto
        """
        # Calcular conservación sin descuentos (hipotética)
        semanas_sin_descuento = analisis.total_semanas_cotizadas + analisis.semanas_descontadas
        conservacion_sin_descuento = semanas_sin_descuento / 4  # Fórmula conservación

        return {
            "resumen_descuentos": analisis.to_dict(),
            "impacto_conservacion": {
                "conservacion_actual_semanas": analisis.total_semanas_cotizadas / 4,
                "conservacion_sin_descuentos_semanas": conservacion_sin_descuento,
                "diferencia_semanas": (conservacion_sin_descuento - (analisis.total_semanas_cotizadas / 4)),
                "impacto_clasificacion": analisis.impacto_conservacion
            },
            "recomendaciones": self._generar_recomendaciones(analisis)
        }

    def _generar_recomendaciones(self, analisis: AnalisisSemanas) -> List[str]:
        """Genera recomendaciones según el impacto de descuentos"""
        recomendaciones = []

        if analisis.semanas_descontadas == 0:
            recomendaciones.append("No hay semanas descontadas que afecten la conservación")

        elif analisis.porcentaje_descuento < 5:
            recomendaciones.append("Descuentos menores, impacto mínimo en conservación")

        elif analisis.porcentaje_descuento < 15:
            recomendaciones.append("Revisar motivos de descuento para posible aclaración en IMSS")

        else:
            recomendaciones.append("⚠️ RECOMENDACIÓN URGENTE: Solicitar revisión de descuentos en IMSS")
            recomendaciones.append("Considerar proceso de aclaración para recuperar semanas")
            recomendaciones.append("Documentar irregularidades en cotización de patrones")

        if analisis.semanas_reintegradas > 0:
            recomendaciones.append("Hay reintegros aplicados correctamente")

        return recomendaciones


if __name__ == "__main__":
    pass


