#!/bin/bash

# Script para aplicar correcciones al flujo de autenticación
# IMSS Pension Analyzer

set -e  # Salir si hay algún error

PROJECT_DIR=~/imss-pension-analyzer/src/frontend
echo "🔧 Aplicando correcciones al flujo de autenticación..."
echo "📂 Directorio del proyecto: $PROJECT_DIR"

# Crear backup
echo ""
echo "📦 Creando backup..."
cd ~/imss-pension-analyzer
tar -czf "backup_frontend_$(date +%Y%m%d_%H%M%S).tar.gz" src/frontend/
echo "✅ Backup creado"

# 1. Crear middleware.ts
echo ""
echo "1️⃣ Creando middleware.ts..."
cat > $PROJECT_DIR/middleware.ts << 'EOF'
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;

  // Rutas públicas
  const publicRoutes = ['/login', '/register'];
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

  // Sin token en ruta protegida -> login
  if (!token && !isPublicRoute) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Con token en ruta pública -> upload
  if (token && isPublicRoute) {
    return NextResponse.redirect(new URL('/upload', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
EOF
echo "✅ middleware.ts creado"

# 2. Actualizar app/(dashboard)/page.tsx
echo ""
echo "2️⃣ Actualizando app/(dashboard)/page.tsx..."
cat > $PROJECT_DIR/app/\(dashboard\)/page.tsx << 'EOF'
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/upload');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Redirigiendo...</p>
      </div>
    </div>
  );
}
EOF
echo "✅ Dashboard page actualizado"

# 3. Actualizar login page
echo ""
echo "3️⃣ Actualizando login page..."
cat > $PROJECT_DIR/app/\(auth\)/login/page.tsx << 'EOF'
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { authAPI } from '@/lib/api';
import { authUtils } from '@/lib/auth';
import { FileText, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('🔐 Intentando login con:', email);
      const response = await authAPI.login({ email, password });
      console.log('✅ Login exitoso');

      authUtils.saveSession(response);
      console.log('✓ Autenticado:', authUtils.isAuthenticated());

      router.replace('/upload');
    } catch (err: any) {
      console.error('❌ Error de login:', err);
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
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
          <CardTitle className="text-2xl font-bold">Análisis IMSS</CardTitle>
          <CardDescription>Ingresa tus credenciales para acceder</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
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
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </Button>

            <div className="text-sm text-center text-gray-600">
              ¿No tienes cuenta?{' '}
              <Link href="/register" className="text-blue-600 hover:underline font-medium">
                Regístrate aquí
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
EOF
echo "✅ Login page actualizado"

# 4. Actualizar register page
echo ""
echo "4️⃣ Actualizando register page..."
cat > $PROJECT_DIR/app/\(auth\)/register/page.tsx << 'EOF'
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { authAPI } from '@/lib/api';
import { authUtils } from '@/lib/auth';
import { FileText, Loader2, CheckCircle2 } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    setLoading(true);

    try {
      console.log('📝 Registrando usuario:', email);
      const response = await authAPI.register({ email, password });
      console.log('✅ Registro exitoso');

      authUtils.saveSession(response);
      router.replace('/upload');
    } catch (err: any) {
      console.error('❌ Error de registro:', err);
      setError(err.response?.data?.detail || 'Error al crear la cuenta');
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
            Regístrate para comenzar a analizar constancias IMSS
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
                {error}
              </div>
            )}

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <CheckCircle2 className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium">Plan Gratuito incluye:</p>
                  <ul className="mt-1 space-y-1 list-disc list-inside">
                    <li>30 análisis mensuales</li>
                    <li>Todas las funciones básicas</li>
                    <li>Exportación a Excel/CSV</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
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
              <Label htmlFor="password">Contraseña</Label>
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
              <Label htmlFor="confirmPassword">Confirmar Contraseña</Label>
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
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
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
EOF
echo "✅ Register page actualizado"

# 5. Actualizar lib/auth.ts
echo ""
echo "5️⃣ Actualizando lib/auth.ts..."
cat > $PROJECT_DIR/lib/auth.ts << 'EOF'
// lib/auth.ts
import Cookies from 'js-cookie';
import type { AuthResponse, User } from '@/types';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export const authUtils = {
  saveSession: (authResponse: AuthResponse) => {
    try {
      console.log('💾 Guardando sesión');
      
      Cookies.set(TOKEN_KEY, authResponse.access_token, { 
        expires: 7,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        path: '/'
      });
      
      if (typeof window !== 'undefined') {
        localStorage.setItem(USER_KEY, JSON.stringify(authResponse.user));
      }
      
      console.log('✅ Sesión guardada correctamente');
    } catch (error) {
      console.error('❌ Error guardando sesión:', error);
      throw error;
    }
  },

  getToken: (): string | undefined => {
    return Cookies.get(TOKEN_KEY);
  },

  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch (error) {
      console.error('Error parseando usuario:', error);
      return null;
    }
  },

  updateUser: (user: User) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  },

  isAuthenticated: (): boolean => {
    return !!Cookies.get(TOKEN_KEY);
  },

  logout: () => {
    console.log('👋 Cerrando sesión');
    Cookies.remove(TOKEN_KEY, { path: '/' });
    if (typeof window !== 'undefined') {
      localStorage.removeItem(USER_KEY);
      window.location.href = '/login';
    }
  },
};
EOF
echo "✅ lib/auth.ts actualizado"

# 6. Verificar estructura de directorios
echo ""
echo "6️⃣ Verificando estructura de directorios..."
echo "Directorios encontrados:"
ls -la $PROJECT_DIR/app/ | grep "^d"
echo ""
ls -la $PROJECT_DIR/app/\(dashboard\)/ 2>/dev/null || echo "⚠️  Directorio (dashboard) no encontrado"

# 7. Resumen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CORRECCIONES APLICADAS EXITOSAMENTE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Cambios realizados:"
echo "   1. ✅ middleware.ts creado (protección de rutas)"
echo "   2. ✅ app/(dashboard)/page.tsx actualizado (redirige a /upload)"
echo "   3. ✅ app/(auth)/login/page.tsx actualizado"
echo "   4. ✅ app/(auth)/register/page.tsx actualizado"
echo "   5. ✅ lib/auth.ts actualizado"
echo ""
echo "🔄 Próximos pasos:"
echo "   1. Reiniciar el servidor de desarrollo:"
echo "      cd ~/imss-pension-analyzer/src/frontend"
echo "      npm run dev"
echo ""
echo "   2. Verificar que el backend esté corriendo:"
echo "      cd ~/imss-pension-analyzer"
echo "      source .venv/bin/activate"
echo "      uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001"
echo ""
echo "   3. Abrir en el navegador: http://localhost:3000"
echo ""
echo "   4. Probar el flujo:"
echo "      - Registro de nuevo usuario → debe redirigir a /upload"
echo "      - Login → debe redirigir a /upload"
echo "      - Acceder a / → debe redirigir a /upload"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""


