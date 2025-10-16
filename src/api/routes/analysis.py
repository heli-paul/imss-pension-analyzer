from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import sys
import os

# Agregar el path del parser original
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'parser'))

from ..database import get_db
from ..services.security import get_current_user, check_usage_limit
from ..services.auth_service import AuthService
from ..services.sheets_service import GoogleSheetsManager
from ..models.user import User

# Importar TODOS los módulos necesarios
from modules.modulo2.historial_laboral import HistorialLaboralExtractor
from correccion_semanas_final import aplicar_correccion_exacta
from calculo_250_semanas import calcular_promedio_250_desde_correccion
from conservacion_derechos import CalculadoraConservacionDerechos
from procesador_semanas_descontadas import ProcesadorSemanasDescontadas
import pdfplumber
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Análisis de Constancias"])

# NO inicializamos GoogleSheetsManager globalmente
# Ahora se inicializa por cada usuario con su propio spreadsheet_id

@router.post("/analizar")
async def analizar_constancia(
    pdf: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analizar constancia IMSS COMPLETA - Réplica exacta del flujo en main.py

    Incluye TODO en el orden correcto:
    1. Historial laboral base
    2. Corrección de empalmes
    3. Semanas descontadas
    4. Conservación de derechos
    5. Promedio salarial 250 semanas
    6. Envío automático al Google Sheet PERSONAL del usuario
    """

    # 1. Verificar límite de uso
    if not check_usage_limit(current_user):
        raise HTTPException(
            status_code=429,
            detail=f"Límite de {current_user.cuota_analisis} análisis alcanzado. Actualiza tu plan."
        )

    # 2. Validar que es PDF
    if not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    try:
        # 3. Leer PDF
        pdf_content = await pdf.read()

        # 4. Extraer texto del PDF (CRÍTICO: se usa en varios pasos)
        texto_completo = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf_doc:
            for page in pdf_doc.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"

        # ========== PROCESAMIENTO COMPLETO (orden del main.py) ==========

        # PASO 1: Extraer historial laboral base
        extractor = HistorialLaboralExtractor()
        datos_base = extractor.procesar_constancia(texto_completo)

        # PASO 2: Aplicar corrección de empalmes (CRÍTICO)
        datos_corregidos = aplicar_correccion_exacta(datos_base)

        # PASO 3: Procesar semanas descontadas
        try:
            procesador_descuentos = ProcesadorSemanasDescontadas()
            analisis_descuentos = procesador_descuentos.procesar_semanas_desde_correccion(datos_corregidos)
            semanas_descontadas = analisis_descuentos.to_dict() if analisis_descuentos else None
        except Exception as e:
            semanas_descontadas = {"error": f"No se pudo procesar: {str(e)}"}

        # PASO 4: Calcular conservación de derechos
        try:
            calculadora_conservacion = CalculadoraConservacionDerechos()
            fecha_emision = datos_corregidos.get('datos_basicos', {}).get('fecha_emision')
            resultado_conservacion = calculadora_conservacion.calcular_conservacion_derechos(
                datos_corregidos=datos_corregidos,
                fecha_emision=fecha_emision
            )
            conservacion = resultado_conservacion.to_dict() if resultado_conservacion else None
        except Exception as e:
            conservacion = {"error": f"No se pudo calcular: {str(e)}"}

        # PASO 5: Calcular promedio 250 semanas (solo para Ley 73)
        ley_aplicable = datos_corregidos.get("datos_basicos", {}).get("ley_aplicable")

        if ley_aplicable == "Ley 73":
            try:
                promedio_250 = calcular_promedio_250_desde_correccion(
                    datos_corregidos=datos_corregidos,
                    fecha_referencia=fecha_emision,
                    debug=True
                )
            except Exception as e:
                promedio_250 = {"error": f"No se pudo calcular: {str(e)}"}
        else:
            promedio_250 = {
                "mensaje": f"El cálculo de 250 semanas solo aplica para Ley 73. Ley aplicable: {ley_aplicable}"
            }

        # ========== NUEVO: ENVIAR AL GOOGLE SHEET PERSONAL DEL USUARIO ==========
        sheets_success = False
        sheets_message = ""
        user_spreadsheet_id = None
        
        # Verificar que el usuario tenga un Google Sheet asignado
        if not current_user.spreadsheet_id:
            logger.warning(f"⚠️ Usuario {current_user.email} no tiene Google Sheet asignado")
            sheets_message = "No tienes un Google Sheet asignado. Contacta al administrador."
        else:
            try:
                logger.info(f"📤 Enviando datos al Google Sheet del usuario {current_user.email}")
                logger.info(f"   📊 Spreadsheet ID: {current_user.spreadsheet_id}")
                
                # Inicializar GoogleSheetsManager con el spreadsheet_id del usuario
                sheets_manager = GoogleSheetsManager(spreadsheet_id=current_user.spreadsheet_id)
                
                datos_completos = {
                    "datos_personales": datos_corregidos.get("datos_basicos", {}),
                    "historial_laboral_corregido": datos_corregidos,
                    "semanas_descontadas": semanas_descontadas,
                    "conservacion_derechos": conservacion,
                    "promedio_salarial_250_semanas": promedio_250
                }
                
                sheets_success, sheets_message = sheets_manager.agregar_constancia_completa(
                    datos=datos_completos,
                    nombre_archivo=pdf.filename
                )
                
                if sheets_success:
                    logger.info(f"✅ {sheets_message}")
                    user_spreadsheet_id = current_user.spreadsheet_id
                else:
                    logger.warning(f"⚠️ {sheets_message}")
                    
            except Exception as e:
                sheets_message = f"Error al enviar a Sheets: {str(e)}"
                logger.error(f"❌ {sheets_message}")

        # 6. Incrementar uso
        auth_service = AuthService(db)
        auth_service.increment_usage(current_user)

        # 7. Retornar resultado COMPLETO
        return {
            "success": True,
            "mensaje": "Constancia procesada exitosamente con análisis completo",
            "archivo": pdf.filename,
            "fecha_procesamiento": datetime.now().isoformat(),
            "usuario": {
                "email": current_user.email,
                "plan": current_user.plan,
                "analisis_usados": current_user.analisis_realizados + 1,
                "analisis_restantes": current_user.cuota_analisis - current_user.analisis_realizados - 1
            },
            "data": {
                "datos_personales": datos_corregidos.get("datos_basicos", {}),
                "historial_laboral_corregido": datos_corregidos,
                "semanas_descontadas": semanas_descontadas,
                "conservacion_derechos": conservacion,
                "promedio_salarial_250_semanas": promedio_250
            },
            # Información de Google Sheets PERSONAL
            "sheets_uploaded": sheets_success,
            "sheets_message": sheets_message,
            "spreadsheet_id": user_spreadsheet_id,
            "spreadsheet_url": current_user.spreadsheet_url if sheets_success else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando constancia: {str(e)}"
        )

@router.get("/mi-uso")
async def ver_mi_uso(current_user: User = Depends(get_current_user)):
    """Ver estadísticas de uso del usuario actual"""

    return {
        "email": current_user.email,
        "plan": current_user.plan,
        "cuota_mensual": current_user.cuota_analisis,
        "analisis_usados": current_user.analisis_realizados,
        "analisis_restantes": current_user.cuota_analisis - current_user.analisis_realizados,
        "porcentaje_uso": round((current_user.analisis_realizados / current_user.cuota_analisis) * 100, 2),
        "google_sheet": {
            "tiene_sheet": bool(current_user.spreadsheet_id),
            "spreadsheet_url": current_user.spreadsheet_url
        }
    }



