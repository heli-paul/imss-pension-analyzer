# debug_app.py - Aplicación simple solo para debug
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import pdfplumber
import io
import json
import re
from datetime import datetime
from typing import Dict, List, Any

# PARSER SIMPLE CON DEBUG
class HistorialLaboralExtractor:
    def __init__(self):
        self.patron_fecha = r'(\d{2}/\d{2}/\d{4})'
        self.patron_salario = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        self.patron_registro = r'([A-Z]\d{9}|\d{10})'

    def debug_web(self, texto_pdf: str) -> Dict[str, Any]:
        """Debug para ver qué está pasando con el texto"""
        
        debug_info = {}

        # Buscar palabras clave básicas
        debug_info["nombre_patron_encontrado"] = "Nombre del patrón" in texto_pdf
        debug_info["registro_patronal_encontrado"] = "Registro Patronal" in texto_pdf
        debug_info["vigente_encontrado"] = "Vigente" in texto_pdf
        debug_info["fechas_encontradas"] = len(re.findall(r'\d{2}/\d{2}/\d{4}', texto_pdf))

        # Muestra del texto (primeros 1000 caracteres)
        debug_info["muestra_texto"] = texto_pdf[:1000]

        # Líneas que contienen info importante
        lineas_importantes = []
        for i, linea in enumerate(texto_pdf.split('\n')):
            if any(palabra in linea for palabra in ['Nombre del patrón', 'Registro Patronal', 'Vigente', 'Fecha de alta', 'Fecha de baja']):
                lineas_importantes.append(f"Línea {i}: {linea.strip()}")

        debug_info["lineas_importantes"] = lineas_importantes[:15]  # Primeras 15

        # Buscar patrones específicos
        patron_completo = r'Nombre del patrón\s+([A-ZÁÉÍÓÚÑ\s,\.&\-]+)\s*Registro Patronal\s+([A-Z]?\d{9,10})\s*Entidad federativa\s+([A-ZÁÉÍÓÚÑ\s]+)\s*Fecha de alta\s+(\d{2}/\d{2}/\d{4})\s*Fecha de baja\s+(?:(\d{2}/\d{2}/\d{4})|Vigente)\s*Salario Base de Cotización \*?\s*\$\s*([\d,\.]+)'
        
        matches = list(re.finditer(patron_completo, texto_pdf, re.MULTILINE | re.DOTALL))
        debug_info["patron_completo_matches"] = len(matches)

        # Patrón más flexible
        patron_flexible = r'Nombre del patrón.*?Registro Patronal.*?(\d{9,10}).*?Fecha de alta.*?(\d{2}/\d{2}/\d{4}).*?Fecha de baja.*?(Vigente|\d{2}/\d{2}/\d{4})'
        matches_flexible = list(re.finditer(patron_flexible, texto_pdf, re.MULTILINE | re.DOTALL | re.IGNORECASE))
        debug_info["patron_flexible_matches"] = len(matches_flexible)

        # Información de matches flexibles
        matches_info = []
        for i, match in enumerate(matches_flexible[:3]):  # Solo primeros 3
            matches_info.append({
                "match_numero": i + 1,
                "registro": match.group(1) if match.group(1) else "",
                "fecha_alta": match.group(2) if match.group(2) else "",
                "fecha_baja": match.group(3) if match.group(3) else "",
                "texto_match": match.group(0)[:300] + "..." if len(match.group(0)) > 300 else match.group(0)
            })
        debug_info["matches_encontrados"] = matches_info

        return debug_info

    def extraer_datos_basicos(self, texto: str) -> Dict[str, Any]:
        """Extrae información básica del asegurado"""
        datos = {}

        # Nombre
        nombre_match = re.search(r'(?:Estimado\(a\),\s*)?([A-ZÁÉÍÓÚÑ\s]+)(?:\s*NSS:|$)', texto, re.MULTILINE)
        if nombre_match:
            datos['nombre'] = nombre_match.group(1).strip()

        # NSS
        nss_match = re.search(r'NSS:\s*(\d{11})', texto)
        if nss_match:
            datos['nss'] = nss_match.group(1)

        # CURP
        curp_match = re.search(r'CURP:\s*([A-Z0-9]{18})', texto)
        if curp_match:
            datos['curp'] = curp_match.group(1)

        # Total de semanas
        semanas_match = re.search(r'Total de semanas cotizadas\s*(\d+)', texto)
        if semanas_match:
            datos['total_semanas'] = int(semanas_match.group(1))

        return datos

    def procesar_constancia_con_debug(self, texto_pdf: str) -> Dict[str, Any]:
        """Procesa la constancia e incluye debug detallado"""
        
        # Extraer datos básicos
        datos_basicos = self.extraer_datos_basicos(texto_pdf)
        
        # Debug detallado
        debug_info = self.debug_web(texto_pdf)
        
        resultado = {
            "exito": True,
            "datos_basicos": datos_basicos,
            "debug_web": debug_info,
            "longitud_texto": len(texto_pdf),
            "fecha_procesamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return resultado

# APLICACIÓN FASTAPI
app = FastAPI(title="Debug IMSS Parser", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Debug IMSS Parser</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .form-group { margin: 20px 0; }
        input[type="file"] { padding: 12px; width: 100%; border: 2px dashed #ddd; border-radius: 4px; }
        button { background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; }
        button:hover { background: #218838; }
        #result { margin-top: 30px; }
        .debug-section { background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
        .success { color: #155724; background: #d4edda; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .error { color: #721c24; background: #f8d7da; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .loading { color: #856404; background: #fff3cd; padding: 15px; border-radius: 4px; margin: 10px 0; }
        pre { white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 4px; }
        .highlight { background: #ffeb3b; padding: 2px 4px; border-radius: 2px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Debug Parser IMSS - Problema Olaf</h1>
        <p>Esta aplicación te ayudará a entender por qué no se detectan los períodos laborales.</p>
        
        <form id="form">
            <div class="form-group">
                <label for="file"><strong>Seleccionar PDF de constancia IMSS:</strong></label>
                <input type="file" id="file" accept=".pdf" required>
            </div>
            <button type="submit">🔬 Analizar con Debug Detallado</button>
        </form>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('form').onsubmit = async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('file');
            const resultDiv = document.getElementById('result');
            
            if (!fileInput.files[0]) {
                resultDiv.innerHTML = '<div class="error">❌ Por favor selecciona un archivo PDF.</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="loading">🔄 Analizando PDF con debug detallado...</div>';
            
            try {
                const formData = new FormData();
                formData.append('pdf', fileInput.files[0]);
                
                const response = await fetch('/analizar-debug', {
                    method: 'POST', 
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    const debugInfo = data.data.debug_web;
                    
                    let html = '<div class="success">✅ Análisis completado</div>';
                    
                    // Información básica
                    html += `<div class="debug-section">
                        <h3>📊 Información Básica</h3>
                        <p><strong>Archivo:</strong> ${data.archivo}</p>
                        <p><strong>Longitud del texto:</strong> ${data.data.longitud_texto} caracteres</p>
                        <p><strong>Nombre detectado:</strong> ${data.data.datos_basicos.nombre || 'No detectado'}</p>
                        <p><strong>NSS:</strong> ${data.data.datos_basicos.nss || 'No detectado'}</p>
                    </div>`;
                    
                    // Búsquedas de palabras clave
                    html += `<div class="debug-section">
                        <h3>🔍 Búsqueda de Palabras Clave</h3>
                        <p><span class="${debugInfo.nombre_patron_encontrado ? 'highlight' : ''}">Nombre del patrón:</span> ${debugInfo.nombre_patron_encontrado ? '✅ Encontrado' : '❌ No encontrado'}</p>
                        <p><span class="${debugInfo.registro_patronal_encontrado ? 'highlight' : ''}">Registro Patronal:</span> ${debugInfo.registro_patronal_encontrado ? '✅ Encontrado' : '❌ No encontrado'}</p>
                        <p><span class="${debugInfo.vigente_encontrado ? 'highlight' : ''}">Vigente:</span> ${debugInfo.vigente_encontrado ? '✅ Encontrado' : '❌ No encontrado'}</p>
                        <p><strong>Fechas encontradas:</strong> ${debugInfo.fechas_encontradas}</p>
                    </div>`;
                    
                    // Matches de patrones
                    html += `<div class="debug-section">
                        <h3>🎯 Resultados de Patrones Regex</h3>
                        <p><strong>Patrón completo:</strong> ${debugInfo.patron_completo_matches} matches</p>
                        <p><strong>Patrón flexible:</strong> ${debugInfo.patron_flexible_matches} matches</p>
                    </div>`;
                    
                    // Matches encontrados
                    if (debugInfo.matches_encontrados && debugInfo.matches_encontrados.length > 0) {
                        html += `<div class="debug-section">
                            <h3>📋 Matches Encontrados</h3>`;
                        
                        debugInfo.matches_encontrados.forEach(match => {
                            html += `<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                                <strong>Match ${match.match_numero}:</strong><br>
                                <strong>Registro:</strong> ${match.registro}<br>
                                <strong>Fecha Alta:</strong> ${match.fecha_alta}<br>
                                <strong>Fecha Baja:</strong> ${match.fecha_baja}<br>
                                <strong>Texto:</strong> <code>${match.texto_match}</code>
                            </div>`;
                        });
                        
                        html += '</div>';
                    }
                    
                    // Líneas importantes
                    if (debugInfo.lineas_importantes && debugInfo.lineas_importantes.length > 0) {
                        html += `<div class="debug-section">
                            <h3>📝 Líneas Importantes del PDF</h3>
                            <pre>${debugInfo.lineas_importantes.join('\\n')}</pre>
                        </div>`;
                    }
                    
                    // Muestra del texto
                    html += `<div class="debug-section">
                        <h3>📄 Primeros 1000 caracteres del PDF</h3>
                        <pre>${debugInfo.muestra_texto}</pre>
                    </div>`;
                    
                    // JSON completo
                    html += `<div class="debug-section">
                        <h3>🔧 JSON Completo (para desarrolladores)</h3>
                        <pre>${JSON.stringify(data.data, null, 2)}</pre>
                    </div>`;
                    
                    resultDiv.innerHTML = html;
                    
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ Error de conexión: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>'''

@app.post("/analizar-debug")
async def analizar_constancia_debug(pdf: UploadFile = File(...)):
    """Endpoint de debug para analizar constancias IMSS"""
    
    try:
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
        
        # Leer PDF
        pdf_content = await pdf.read()
        
        # Extraer texto
        texto_completo = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf_doc:
            for page_num, page in enumerate(pdf_doc.pages):
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo += f"\n--- PÁGINA {page_num + 1} ---\n"
                    texto_completo += texto_pagina + "\n"
        
        # Analizar con debug
        extractor = HistorialLaboralExtractor()
        resultado = extractor.procesar_constancia_con_debug(texto_completo)
        
        return {
            "success": True,
            "mensaje": "Debug completado",
            "archivo": pdf.filename,
            "data": resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)


