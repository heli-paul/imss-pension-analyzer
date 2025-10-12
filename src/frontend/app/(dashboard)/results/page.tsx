'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Share2, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import Cookies from 'js-cookie';

export default function ResultsPage() {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<any>(null);
  const [compartiendo, setCompartiendo] = useState(false);
  const [compartido, setCompartido] = useState(false);

  const formatearFecha = (fechaISO: string | null | undefined): string => {
    if (!fechaISO) return 'N/A';

    try {
      // Si ya está en formato DD/MM/YYYY, no tocar
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(fechaISO)) {
        return fechaISO;
      }

      // Para ISO (YYYY-MM-DD o full ISO con T), parsear componentes manualmente
      let year: number, month: number, day: number;
      if (fechaISO.includes('T')) {
        // Full ISO: tomar solo la parte de fecha
        const fechaPart = fechaISO.split('T')[0];
        [year, month, day] = fechaPart.split('-').map(Number);
      } else if (fechaISO.includes('-')) {
        // Simple YYYY-MM-DD
        [year, month, day] = fechaISO.split('-').map(Number);
      } else {
        // Fallback a new Date si no es ISO
        const fecha = new Date(fechaISO);
        if (isNaN(fecha.getTime())) {
          return fechaISO;
        }
        const dia = String(fecha.getDate()).padStart(2, '0');
        const mes = String(fecha.getMonth() + 1).padStart(2, '0');
        const año = fecha.getFullYear();
        return `${dia}/${mes}/${año}`;
      }

      // Crear Date con componentes locales (evita shift de timezone)
      const fecha = new Date(year, month - 1, day);

      // Verificar si es válida
      if (isNaN(fecha.getTime())) {
        return fechaISO;
      }

      const dia = String(fecha.getDate()).padStart(2, '0');
      const mes = String(fecha.getMonth() + 1).padStart(2, '0');
      const año = fecha.getFullYear();
      return `${dia}/${mes}/${año}`;
    } catch {
      return fechaISO;
    }
  };

  useEffect(() => {
    const data = localStorage.getItem('ultimo_analisis');
    if (!data) {
      router.push('/upload');
      return;
    }
    try {
      const parsed = JSON.parse(data);
      setAnalysis(parsed);

      if (parsed.spreadsheet_url) {
        setCompartido(true);
      }
    } catch (error) {
      console.error('Error parseando datos:', error);
      router.push('/upload');
    }
  }, [router]);

  const compartirAGoogleSheets = async () => {
    if (!analysis) return;

    setCompartiendo(true);
    try {
      const token = Cookies.get('token');

      const userResponse = await axios.get(
        'http://localhost:8001/api/auth/my-sheet',
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!userResponse.data.has_sheet) {
        await axios.post(
          'http://localhost:8001/api/auth/create-sheet',
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      setCompartido(true);

      const updatedAnalysis = {
        ...analysis,
        spreadsheet_url: userResponse.data.spreadsheet_url
      };
      localStorage.setItem('ultimo_analisis', JSON.stringify(updatedAnalysis));
      setAnalysis(updatedAnalysis);

      alert('✅ Datos compartidos a tu Google Sheet exitosamente');

    } catch (error: any) {
      console.error('Error compartiendo:', error);
      alert('❌ Error al compartir a Google Sheets');
    } finally {
      setCompartiendo(false);
    }
  };

  if (!analysis) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const datos = analysis.data || {};
  const datosPersonales = datos.datos_personales || {};
  const semanasDesc = datos.semanas_descontadas || {};
  const conservacion = datos.conservacion_derechos || {};
  const promedio250 = datos.promedio_salarial_250_semanas || {};
  const resumenCotizaciones = datos.resumen_cotizaciones || {};

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle2 className="w-8 h-8 text-green-600" />
            <h1 className="text-3xl font-bold">Resultados del Análisis</h1>
          </div>
          <p className="text-gray-600">{analysis.file_name || analysis.archivo || 'constancia.pdf'}</p>
        </div>
        <div className="flex gap-3">
          {!compartido ? (
            <Button onClick={compartirAGoogleSheets} disabled={compartiendo}>
              {compartiendo ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Compartiendo...
                </>
              ) : (
                <>
                  <Share2 className="mr-2 h-5 w-5" />
                  Compartir a Google Sheets
                </>
              )}
            </Button>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">✓ Compartido en Sheets</span>
            </div>
          )}
          <Button onClick={() => router.push('/upload')} variant="outline">
            Nuevo Análisis
          </Button>
        </div>
      </div>

      {/* INFORMACIÓN DEL TRABAJADOR */}
      <Card>
        <CardHeader className="bg-blue-50">
          <CardTitle>📋 Información del Trabajador</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 gap-4 font-mono text-sm">
            <div><span className="text-red-600">nss:</span> {datosPersonales.nss || 'N/A'}</div>
            <div><span className="text-red-600">curp:</span> {datosPersonales.curp || 'N/A'}</div>
            <div className="col-span-2"><span className="text-red-600">nombre:</span> {datosPersonales.nombre || 'N/A'}</div>
            <div><span className="text-red-600">fecha_nacimiento:</span> {formatearFecha(datosPersonales.fecha_nacimiento)}</div>
            <div><span className="text-red-600">edad:</span> {datosPersonales.edad || 'N/A'} años</div>
            <div><span className="text-red-600">fecha_emision:</span> {formatearFecha(datosPersonales.fecha_emision)}</div>
            <div><span className="text-red-600">ley_aplicable:</span> {datosPersonales.ley_aplicable || 'N/A'}</div>
            <div><span className="text-red-600">fecha_primer_alta:</span> {datosPersonales.fecha_primer_alta || 'N/A'}</div>
            <div><span className="text-red-600">anos_cotizando_antes_1997:</span> {datosPersonales.anos_cotizando_antes_1997 || 0}</div>
          </div>
        </CardContent>
      </Card>

      {/* RESUMEN DE COTIZACIONES */}
      {resumenCotizaciones && Object.keys(resumenCotizaciones).length > 0 && (
        <Card>
          <CardHeader className="bg-indigo-50">
            <CardTitle>📈 Resumen de Semanas Utilizadas</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              <div className="p-4 bg-blue-50 rounded">
                <p className="text-xs text-gray-600">Semanas Utilizadas en Cálculo</p>
                <p className="text-2xl font-bold text-blue-600">{resumenCotizaciones.semanas_utilizadas_calculo}</p>
              </div>
              <div className="p-4 bg-green-50 rounded">
                <p className="text-xs text-gray-600">Semanas IMSS Oficial</p>
                <p className="text-2xl font-bold text-green-600">{resumenCotizaciones.semanas_cotizadas_imss}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded">
                <p className="text-xs text-gray-600">Total Oficial IMSS</p>
                <p className="text-2xl font-bold text-purple-600">{resumenCotizaciones.total_semanas_cotizadas_oficial}</p>
              </div>
            </div>
            <div className="font-mono text-sm">
              <div><span className="text-red-600">precision_calculo:</span> {resumenCotizaciones.precision_calculo}</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ANÁLISIS DE SEMANAS DESCONTADAS */}
      <Card>
        <CardHeader className="bg-green-50">
          <CardTitle>📊 Análisis de Semanas Descontadas</CardTitle>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded">
              <p className="text-xs text-gray-600">Semanas cotizadas IMSS</p>
              <p className="text-2xl font-bold text-blue-600">{semanasDesc.semanas_cotizadas_imss || 0}</p>
            </div>
            <div className="p-4 bg-red-50 rounded">
              <p className="text-xs text-gray-600">Descontadas</p>
              <p className="text-2xl font-bold text-red-600">{semanasDesc.semanas_descontadas || 0}</p>
            </div>
            <div className="p-4 bg-green-50 rounded">
              <p className="text-xs text-gray-600 font-semibold">Total de semanas cotizadas</p>
              <p className="text-2xl font-bold text-green-600">{semanasDesc.total_semanas_cotizadas || 0}</p>
            </div>
            <div className="p-4 bg-purple-50 rounded">
              <p className="text-xs text-gray-600">Reintegradas</p>
              <p className="text-2xl font-bold text-purple-600">{semanasDesc.semanas_reintegradas || 0}</p>
            </div>
          </div>
          <div className="font-mono text-sm">
            <div><span className="text-red-600">porcentaje_descuento:</span> {semanasDesc.porcentaje_descuento || 0}%</div>
          </div>
          {semanasDesc.observaciones && semanasDesc.observaciones.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded border-l-4 border-blue-500">
              <p className="font-semibold text-sm mb-2">Observaciones:</p>
              {semanasDesc.observaciones
                .filter((obs: string) => !obs.toLowerCase().includes('empalme'))
                .map((obs: string, idx: number) => (
                  <p key={idx} className="text-sm text-gray-700">• {obs}</p>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* CONSERVACIÓN DE DERECHOS */}
      <Card>
        <CardHeader className="bg-yellow-50">
          <CardTitle>⚖️ Conservación de Derechos</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="font-mono text-sm space-y-2">
            <div><span className="text-red-600">ley_aplicable:</span> {conservacion.ley_aplicable || 'N/A'}</div>
            <div><span className="text-red-600">semanas_reconocidas:</span> {conservacion.semanas_reconocidas || 0}</div>
            <div><span className="text-red-600">años_cotizados:</span> {conservacion.años_cotizados?.toFixed(2) || 0}</div>
            <div><span className="text-red-600">conservacion_años:</span> {conservacion.conservacion_años?.toFixed(2) || 0}</div>
            <div><span className="text-red-600">conservacion_dias:</span> {conservacion.conservacion_dias || 0}</div>
            <div><span className="text-red-600">fecha_ultima_baja:</span> {formatearFecha(conservacion.fecha_ultima_baja)}</div>
            <div><span className="text-red-600">fecha_vencimiento:</span> {formatearFecha(conservacion.fecha_vencimiento)}</div>
            <div><span className="text-red-600">esta_vigente:</span> {conservacion.esta_vigente || 'N/A'}</div>
            <div><span className="text-red-600">puede_reactivar:</span> {conservacion.puede_reactivar || 'N/A'}</div>
          </div>
          {conservacion.esta_vigente && (
            <div className={`mt-4 p-4 rounded-lg ${
              conservacion.esta_vigente === 'Sí'
                ? 'bg-green-100 border-2 border-green-300'
                : 'bg-red-100 border-2 border-red-300'
            }`}>
              <p className="font-bold">
                Estado: {conservacion.esta_vigente === 'Sí' ? '✓ Vigente' : '✗ No Vigente'}
              </p>
            </div>
          )}
          {conservacion.leyendas && conservacion.leyendas.length > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 rounded border-l-4 border-yellow-500">
              <p className="font-semibold text-sm mb-2">⚠️ Información Importante:</p>
              {conservacion.leyendas.map((leyenda: string, idx: number) => (
                <p key={idx} className="text-sm text-gray-700">• {leyenda}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* PROMEDIO 250 SEMANAS */}
      {promedio250 && !promedio250.error && Object.keys(promedio250).length > 0 && (
        <Card>
          <CardHeader className="bg-purple-50">
            <CardTitle>💰 Promedio Salarial (250 Semanas)</CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border-2 border-green-200">
                <p className="text-xs text-gray-600 mb-1">Salario Promedio Diario</p>
                <p className="text-4xl font-bold text-green-600">
                  ${promedio250.salario_promedio_diario?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border-2 border-blue-200">
                <p className="text-xs text-gray-600 mb-1">Salario Promedio Mensual</p>
                <p className="text-4xl font-bold text-blue-600">
                  ${promedio250.salario_promedio_mensual?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
            <div className="font-mono text-sm space-y-2">
              <div><span className="text-red-600">tiene_250_semanas_completas:</span> {promedio250.tiene_250_semanas_completas || 'N/A'}</div>
              <div><span className="text-red-600">total_dias_calculados:</span> {promedio250.total_dias_calculados || 0}</div>
              <div><span className="text-red-600">fecha_inicio_ventana:</span> {formatearFecha(promedio250.fecha_inicio_ventana)}</div>
              <div><span className="text-red-600">fecha_fin_ventana:</span> {formatearFecha(promedio250.fecha_fin_ventana)}</div>
            </div>
            {promedio250.observaciones && promedio250.observaciones.length > 0 && (
              <div className="mt-4 p-3 bg-yellow-50 rounded border-l-4 border-yellow-500">
                <p className="font-semibold text-sm mb-2">⚠️ Observaciones:</p>
                {promedio250.observaciones
                  .filter((obs: string) => !obs.toLowerCase().includes('empalme'))
                  .map((obs: string, idx: number) => (
                    <p key={idx} className="text-sm text-gray-700">• {obs}</p>
                  ))}
              </div>
            )}
            {promedio250.segmentos_utilizados && promedio250.segmentos_utilizados.length > 0 && (
              <div className="mt-4">
                <p className="font-semibold text-sm mb-3">Detalle por segmento:</p>
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto max-h-96">
                  <pre className="whitespace-pre-wrap">
{promedio250.segmentos_utilizados.join('\n')}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      {analysis.usuario && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-center text-sm text-gray-600">
              <div>
                <p>Usuario: {analysis.usuario.email || 'N/A'} | Plan: {analysis.usuario.plan || 'N/A'}</p>
                <p>Análisis restantes: {analysis.usuario.analisis_restantes || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}


