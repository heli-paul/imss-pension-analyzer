"""
Módulo 1: Basic Data Extractor
Extrae datos básicos del PDF: información personal, semanas, y ley aplicable
NOMENCLATURA: Exacta de la constancia oficial IMSS
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BasicDataResult(BaseModel):
    """Resultado de extracción de datos básicos - NOMENCLATURA OFICIAL IMSS"""
    # Metadatos
    fecha_procesamiento: str
    archivo: str

    # Datos personales
    nombre: Optional[str] = None
    nss: Optional[str] = None
    curp: Optional[str] = None
    fecha_emision: Optional[str] = None
    fecha_nacimiento: Optional[str] = None  # ✅ NUEVO
    edad: Optional[int] = None              # ✅ NUEVO

    # ✅ NOMENCLATURA OFICIAL IMSS - Exacta de la constancia
    semanas_cotizadas_imss: Optional[int] = None      # "Semanas cotizadas IMSS"
    semanas_descontadas: Optional[int] = None          # "Semanas Descontadas"
    semanas_reintegradas: Optional[int] = None         # "Semanas Reintegradas"
    total_semanas_cotizadas: Optional[int] = None      # "Total de semanas cotizadas"

    # Ley aplicable
    ley_aplicable: str = "indeterminado"
    fecha_primer_alta: Optional[str] = None
    anos_cotizando_antes_1997: float = 0.0

    # Errores
    errors: list = []

class BasicDataExtractor:
    """
    Extractor de datos básicos del PDF IMSS
    REGLA: SOLO EXTRAE, NUNCA CALCULA NI MODIFICA
    """

    def __init__(self):
        self.patterns = {
            'nss': [
                r'NSS:\s*(\d{11})',
                r'NSS\s+(\d{11})',
                r'Número de Seguridad Social:\s*(\d{11})'
            ],
            'curp': [
                r'CURP:\s*([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})',
                r'CURP\s+([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})'
            ],
            'nombre': [
                r'reporte\s*\n.*?\n\s*([A-ZÁÉÍÓÚÑ\s]+[A-ZÁÉÍÓÚÑ])\s*\n',
                r'Estimado\(a\),?\s*\n\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'Asegurado:\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'NOMBRE:\s*([A-ZÁÉÍÓÚÑ\s]+)',
                r'([A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,})',
            ],
            'fecha_emision': [
                r'Fecha de emisión.*?(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
                r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
                r'reporte\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',
            ]
        }

    def extract_basic_data(self, pdf_text: str, filename: str) -> BasicDataResult:
        """
        Extrae todos los datos básicos del PDF
        REGLA DE ORO: Solo extrae, NUNCA calcula ni modifica
        """
        resultado = BasicDataResult(
            fecha_procesamiento=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            archivo=filename
        )

        try:
            # Extraer información personal
            self._extract_personal_info(pdf_text, resultado)

            # Extraer semanas (SOLO extracción)
            self._extract_semanas_info(pdf_text, resultado)

            # Determinar ley aplicable
            self._determine_ley_aplicable(pdf_text, resultado)

            # Validar datos extraídos
            self._validate_basic_data(resultado)

            logger.info(f"✅ Datos básicos extraídos: NSS={resultado.nss}, "
                       f"IMSS={resultado.semanas_cotizadas_imss}, "
                       f"Total={resultado.total_semanas_cotizadas}, Ley={resultado.ley_aplicable}")

        except Exception as e:
            logger.error(f"Error extrayendo datos básicos: {e}")
            resultado.errors.append(f"Error en extracción básica: {str(e)}")

        return resultado

    def _extract_personal_info(self, text: str, resultado: BasicDataResult):
        """Extrae NSS, CURP, nombre y fecha de emisión"""

        # NSS
        for pattern in self.patterns['nss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                resultado.nss = match.group(1)
                break

        # CURP
        for pattern in self.patterns['curp']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                resultado.curp = match.group(1)
                break

        # ✅ NUEVO: Extraer fecha de nacimiento del CURP
        if resultado.curp:
            fecha_nac = self._extraer_fecha_nacimiento_de_curp(resultado.curp)
            if fecha_nac:
                resultado.fecha_nacimiento = fecha_nac
                resultado.edad = self._calcular_edad(fecha_nac)

        # Nombre
        for pattern in self.patterns['nombre']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                nombre_candidato = match.group(1).strip()
                if len(nombre_candidato.split()) >= 2:
                    resultado.nombre = self._clean_name(nombre_candidato)
                    break

        # Fecha de emisión
        for pattern in self.patterns['fecha_emision']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dia, mes, año = match.groups()
                resultado.fecha_emision = f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
                break
    def _extraer_fecha_nacimiento_de_curp(self, curp: str) -> Optional[str]:
        """
        Extrae fecha de nacimiento del CURP
        Formato CURP: LLLLAAММDDHHEEECCD
        Posiciones: 0-3=Letras, 4-5=Año, 6-7=Mes, 8-9=Día
        Ejemplo: SAFO830624HTLNRL08
                 SAFO 83 06 24 ...
        """
        if not curp or len(curp) < 18:
            return None
    
        try:
            # Extraer AA, MM, DD del CURP
            año_2_digitos = int(curp[4:6])    # 83
            mes = curp[6:8]                    # 06
            dia = curp[8:10]                   # 24
        
            # Determinar siglo
            # Si año >= 00 y <= 25, asumir 2000s
            # Si año >= 26 y <= 99, asumir 1900s
            if año_2_digitos <= 25:
                año_completo = 2000 + año_2_digitos
            else:
                año_completo = 1900 + año_2_digitos
        
            # Para tu ejemplo: 83 -> 1983 ✓
        
            # Validar que la fecha sea válida
            fecha_nacimiento = datetime.strptime(f"{año_completo}-{mes}-{dia}", "%Y-%m-%d")
        
            # Verificar que no sea futuro
            if fecha_nacimiento > datetime.now():
                año_completo -= 100
                fecha_nacimiento = datetime.strptime(f"{año_completo}-{mes}-{dia}", "%Y-%m-%d")
        
            return fecha_nacimiento.strftime("%Y-%m-%d")
        
        except Exception as e:
            logger.error(f"Error extrayendo fecha de nacimiento del CURP {curp}: {e}")
            return None

    def _calcular_edad(self, fecha_nacimiento_str: str) -> Optional[int]:
        """Calcula edad a partir de fecha de nacimiento"""
        if not fecha_nacimiento_str:
            return None
        
        try:
            fecha_nac = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d")
            hoy = datetime.now()
            edad = hoy.year - fecha_nac.year
            
            # Ajustar si aún no ha cumplido años este año
            if (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day):
                edad -= 1
            
            return edad
        except Exception as e:
            logger.error(f"Error calculando edad: {e}")
            return None

    def _extract_semanas_info(self, text: str, resultado: BasicDataResult):
        """
        Extrae información de semanas - SOLO EXTRACCIÓN, NO CÁLCULO
        Nomenclatura oficial IMSS
        """
        try:
            # Buscar "Total de semanas cotizadas" (aparece arriba en la constancia)
            patterns_total = [
                r'Total\s+de\s+semanas\s+cotizadas\s*[:\n\s]*(\d+)',
                r'Total.*?cotizadas.*?\n\s*(\d+)',
                r'DD\s+MM\s+YYYY\s*\n\s*(\d+)',
            ]

            for pattern in patterns_total:
                match_total = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match_total:
                    resultado.total_semanas_cotizadas = int(match_total.group(1))
                    logger.info(f"✅ Total semanas cotizadas extraído: {resultado.total_semanas_cotizadas}")
                    break

            # Buscar sección "Tu detalle de semanas cotizadas"
            detalle_pattern = r'Tu\s+detalle\s+de\s+semanas.*?(\d+)\s+(\d+)\s+(\d+)'
            match_detalle = re.search(detalle_pattern, text, re.IGNORECASE | re.DOTALL)

            if match_detalle:
                resultado.semanas_cotizadas_imss = int(match_detalle.group(1))
                resultado.semanas_descontadas = int(match_detalle.group(2))
                resultado.semanas_reintegradas = int(match_detalle.group(3))

                logger.info(f"✅ Detalle extraído: IMSS={resultado.semanas_cotizadas_imss}, "
                          f"Descontadas={resultado.semanas_descontadas}, "
                          f"Reintegradas={resultado.semanas_reintegradas}")

            # Si no se encontró, usar valores por defecto
            if not resultado.semanas_descontadas:
                resultado.semanas_descontadas = 0
            if not resultado.semanas_reintegradas:
                resultado.semanas_reintegradas = 0

        except Exception as e:
            logger.error(f"Error extrayendo semanas: {e}")
            resultado.errors.append(f"Error en semanas: {str(e)}")

    def _determine_ley_aplicable(self, text: str, resultado: BasicDataResult):
        """Determina qué ley aplica basado en fecha de primer alta"""

        try:
            # Buscar fecha de primer alta en el texto
            fecha_primer_alta = self._extract_fecha_primer_alta(text)

            if fecha_primer_alta:
                resultado.fecha_primer_alta = fecha_primer_alta

                # Convertir a objeto datetime para comparación
                fecha_alta_obj = datetime.strptime(fecha_primer_alta, '%Y-%m-%d')
                fecha_limite_ley97 = datetime(1997, 7, 1)

                if fecha_alta_obj < fecha_limite_ley97:
                    resultado.ley_aplicable = "Ley 73"
                    años_antes_97 = (fecha_limite_ley97 - fecha_alta_obj).days / 365.25
                    resultado.anos_cotizando_antes_1997 = round(años_antes_97, 1)
                else:
                    resultado.ley_aplicable = "Ley 97"
                    resultado.anos_cotizando_antes_1997 = 0.0

        except Exception as e:
            logger.error(f"Error determinando ley aplicable: {e}")
            resultado.errors.append(f"Error en ley aplicable: {str(e)}")

    def _extract_fecha_primer_alta(self, text: str) -> Optional[str]:
        """Extrae fecha de primer alta del PDF"""
        patrones_alta = [
            r'Fecha\s+de\s+alta\s+(\d{2}/\d{2}/\d{4})',
            r'ALTA\s+(\d{2}/\d{2}/\d{4})',
            r'Alta:\s*(\d{2}/\d{2}/\d{4})',
        ]

        fechas_encontradas = []

        for patron in patrones_alta:
            matches = re.finditer(patron, text, re.IGNORECASE)
            for match in matches:
                fecha_str = match.group(1)
                try:
                    fecha_obj = datetime.strptime(fecha_str, '%d/%m/%Y')
                    fechas_encontradas.append(fecha_obj)
                except:
                    continue

        if fechas_encontradas:
            fecha_mas_antigua = min(fechas_encontradas)
            return fecha_mas_antigua.strftime('%Y-%m-%d')

        return None

    def _clean_name(self, name_text: str) -> str:
        """Limpia el nombre extraído"""
        if not name_text:
            return ""

        cleaned = re.sub(r'\s+', ' ', name_text.strip())

        unwanted_patterns = [
            r'asegurado\s*:?\s*',
            r'nombre\s*:?\s*',
            r'del\s+asegurado\s*:?\s*',
            r'\s+dd\s+mm\s+yyyy\s*$',
            r'\s+dd\s+mm\s+aaaa\s*$',
        ]

        for pattern in unwanted_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    def _validate_basic_data(self, resultado: BasicDataResult):
        """Valida los datos básicos extraídos"""

        # Validar NSS
        if resultado.nss and len(resultado.nss) != 11:
            resultado.errors.append(f"NSS inválido: {resultado.nss}")

        # Validar CURP
        if resultado.curp and len(resultado.curp) != 18:
            resultado.errors.append(f"CURP inválido: {resultado.curp}")

        # Validar semanas
        if resultado.semanas_cotizadas_imss and resultado.semanas_cotizadas_imss > 3000:
            resultado.errors.append(f"Semanas IMSS muy altas: {resultado.semanas_cotizadas_imss}")

        # Validar que los datos oficiales coincidan con la fórmula IMSS
        if all([resultado.semanas_cotizadas_imss, resultado.total_semanas_cotizadas]):
            total_esperado = (resultado.semanas_cotizadas_imss -
                            resultado.semanas_descontadas +
                            resultado.semanas_reintegradas)

            if abs(total_esperado - resultado.total_semanas_cotizadas) > 1:
                logger.warning(
                    f"⚠️ Discrepancia en datos oficiales: "
                    f"{resultado.semanas_cotizadas_imss} - {resultado.semanas_descontadas} + "
                    f"{resultado.semanas_reintegradas} = {total_esperado}, "
                    f"pero IMSS reporta {resultado.total_semanas_cotizadas}"
                )

def extract_basic_data_from_pdf(pdf_text: str, filename: str) -> Dict[str, Any]:
    """
    Función principal para extraer datos básicos
    Retorna diccionario con nomenclatura oficial IMSS
    """
    extractor = BasicDataExtractor()
    resultado = extractor.extract_basic_data(pdf_text, filename)

    return {
        "fecha_procesamiento": resultado.fecha_procesamiento,
        "archivo": resultado.archivo,
        "nombre": resultado.nombre,
        "nss": resultado.nss,
        "curp": resultado.curp,
        "fecha_emision": resultado.fecha_emision,
        "fecha_nacimiento": resultado.fecha_nacimiento,  # ✅ NUEVO
        "edad": resultado.edad,                          # ✅ NUEVO
        "semanas_cotizadas_imss": resultado.semanas_cotizadas_imss,
        "semanas_descontadas": resultado.semanas_descontadas,
        "semanas_reintegradas": resultado.semanas_reintegradas,
        "total_semanas_cotizadas": resultado.total_semanas_cotizadas,
        "ley_aplicable": resultado.ley_aplicable,
        "fecha_primer_alta": resultado.fecha_primer_alta,
        "anos_cotizando_antes_1997": resultado.anos_cotizando_antes_1997,
        "errors": resultado.errors
    }


