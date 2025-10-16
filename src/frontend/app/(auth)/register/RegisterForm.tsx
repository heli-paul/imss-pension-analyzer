'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { authAPI } from '@/lib/api';
import { authUtils } from '@/lib/auth';
import { FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [invitationToken, setInvitationToken] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tokenFromUrl, setTokenFromUrl] = useState(false);

  // Capturar token del URL al cargar
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setInvitationToken(token);
      setTokenFromUrl(true);
      console.log('✅ Token de invitación capturado del URL');
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validaciones
    if (!invitationToken) {
      setError('Se requiere un código de invitación válido');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    if (!fullName.trim()) {
      setError('El nombre completo es requerido');
      return;
    }

    setLoading(true);

    try {
      console.log('📝 Registrando usuario:', email);
      const response = await authAPI.register({ 
        email, 
        password,
        full_name: fullName,
        company_name: companyName || undefined,
        invitation_token: invitationToken
      });
      console.log('✅ Registro exitoso');

      authUtils.saveSession(response);
      router.replace('/upload');
    } catch (err: any) {
      console.error('❌ Error de registro:', err);
      const errorMessage = err.response?.data?.detail || 'Error al crear la cuenta';
      setError(errorMessage);
      
      // Si el error es del token, permitir editarlo
      if (errorMessage.includes('token') || errorMessage.includes('invitación')) {
        setTokenFromUrl(false);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Crear Cuenta</CardTitle>
          <CardDescription>
            {tokenFromUrl 
              ? '¡Bienvenido! Completa tus datos para activar tu cuenta'
              : 'Necesitas un código de invitación para registrarte'
            }
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {tokenFromUrl && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-green-900">
                    <p className="font-medium">✓ Invitación válida</p>
                    <p className="text-xs mt-1">Completa el formulario para activar tu cuenta</p>
                  </div>
                </div>
              </div>
            )}

            {/* Mostrar campo de token solo si no vino por URL o hubo error */}
            {!tokenFromUrl && (
              <div className="space-y-2">
                <Label htmlFor="invitationToken">Código de Invitación *</Label>
                <Input
                  id="invitationToken"
                  type="text"
                  placeholder="Pega tu código de invitación aquí"
                  value={invitationToken}
                  onChange={(e) => setInvitationToken(e.target.value)}
                  required
                  disabled={loading}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500">
                  Recibiste este código por email. Si no lo tienes, contacta al administrador.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fullName">Nombre Completo *</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Juan Pérez"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="companyName">Empresa (opcional)</Label>
              <Input
                id="companyName"
                type="text"
                placeholder="Nombre de tu empresa"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Contraseña *</Label>
              <Input
                id="password"
                type="password"
                placeholder="Mínimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                minLength={8}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirmar Contraseña *</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Repite tu contraseña"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <CheckCircle2 className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium">Tu plan incluye:</p>
                  <ul className="mt-1 space-y-1 text-xs">
                    <li>✓ 30 análisis mensuales</li>
                    <li>✓ Exportación a Excel/CSV</li>
                    <li>✓ Todas las funciones básicas</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading || !invitationToken}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creando cuenta...
                </>
              ) : (
                'Crear Cuenta'
              )}
            </Button>

            <div className="text-sm text-center text-gray-600">
              ¿Ya tienes cuenta?{' '}
              <Link href="/login" className="text-blue-600 hover:underline font-medium">
                Inicia sesión aquí
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
