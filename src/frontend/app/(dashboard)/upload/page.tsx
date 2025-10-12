'use client';

import { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { analysisAPI } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validar tipo de archivo
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (!validTypes.includes(selectedFile.type)) {
        setError('Solo se permiten archivos PDF o imágenes (PNG, JPG, JPEG)');
        setFile(null);
        return;
      }

      // Validar tamaño (máximo 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('El archivo no debe superar los 10MB');
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setError('');
      setSuccess(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Por favor selecciona un archivo');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess(false);

    try {
      console.log('📤 Subiendo archivo:', file.name);
      const result = await analysisAPI.uploadFile(file);
      console.log('✅ Archivo procesado:', result);
      
      // Guardar resultado en localStorage (temporalmente)
      localStorage.setItem('ultimo_analisis', JSON.stringify(result));
      
      setSuccess(true);
      setFile(null);
      
      // Limpiar el input file
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      // Redirigir a resultados después de 1 segundo
      setTimeout(() => {
        window.location.href = '/results';
      }, 1000);

    } catch (err: any) {
      console.error('❌ Error subiendo archivo:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          'Error al procesar el archivo';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Subir Constancia IMSS
        </h1>
        <p className="text-gray-600">
          Sube tu constancia de semanas cotizadas en formato PDF o imagen para analizarla
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Seleccionar Archivo
          </CardTitle>
          <CardDescription>
            Formatos permitidos: PDF, PNG, JPG (máximo 10MB)
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Mensaje de error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">Error</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
                <button
                  onClick={() => setError('')}
                  className="text-red-400 hover:text-red-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Mensaje de éxito */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">¡Éxito!</p>
                  <p className="text-sm text-green-700 mt-1">
                    Archivo procesado exitosamente. Redirigiendo a resultados...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Área de selección de archivo */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            
            <label
              htmlFor="file-upload"
              className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium"
            >
              Haz clic para seleccionar un archivo
            </label>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <p className="text-sm text-gray-500 mt-2">
              o arrastra y suelta aquí
            </p>
          </div>

          {/* Información del archivo seleccionado */}
          {file && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <FileText className="w-8 h-8 text-blue-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                {!uploading && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setFile(null);
                      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
                      if (fileInput) fileInput.value = '';
                    }}
                  >
                    Cambiar
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Botón de subir */}
          <Button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Procesando archivo...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-5 w-5" />
                Subir y Analizar
              </>
            )}
          </Button>

          {/* Información adicional */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm text-gray-600">
            <p className="font-medium text-gray-900">📋 Información:</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>El análisis puede tardar unos segundos</li>
              <li>Asegúrate de que la constancia sea legible</li>
              <li>Los datos se guardarán en tu cuenta</li>
              <li>Podrás exportar los resultados a Excel</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Card de ayuda */}
      <Card className="mt-6 bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-lg">💡 ¿Necesitas ayuda?</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700">
            Si tu constancia tiene múltiples páginas, asegúrate de subirla completa en un solo archivo PDF.
            Para mejores resultados, la imagen debe ser clara y sin manchas.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}


