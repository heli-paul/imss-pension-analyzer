// src/frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;
  
  // Si está accediendo a /admin, dejar pasar siempre (con o sin token)
  if (pathname.startsWith('/admin')) {
    return NextResponse.next();
  }
  
  // Rutas públicas que no requieren autenticación
  const publicRoutes = ['/login', '/register', '/invite', '/signup'];
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));
  
  // Si no hay token y está intentando acceder a una ruta protegida
  if (!token && !isPublicRoute) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
  
  // Si hay token y está en login/register, redirigir a upload
  if (token && isPublicRoute) {
    const uploadUrl = new URL('/upload', request.url);
    return NextResponse.redirect(uploadUrl);
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
