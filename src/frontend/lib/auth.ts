// src/frontend/lib/auth.ts
import Cookies from 'js-cookie';
import type { AuthResponse, User } from '@/types';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export const authUtils = {
  // Guardar sesión después del login/register
  saveSession: (authResponse: AuthResponse) => {
    try {
      console.log('💾 Guardando sesión:', authResponse);
      
      // Guardar token en cookie (7 días de expiración)
      Cookies.set(TOKEN_KEY, authResponse.access_token, { 
        expires: 7,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        path: '/'
      });
      
      // Guardar usuario en localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(USER_KEY, JSON.stringify(authResponse.user));
      }
      
      console.log('✅ Sesión guardada correctamente');
      console.log('Token en cookie:', Cookies.get(TOKEN_KEY) ? 'Sí' : 'No');
      console.log('Usuario en localStorage:', localStorage.getItem(USER_KEY) ? 'Sí' : 'No');
      
    } catch (error) {
      console.error('❌ Error guardando sesión:', error);
      throw error;
    }
  },

  // Obtener token
  getToken: (): string | undefined => {
    return Cookies.get(TOKEN_KEY);
  },

  // Obtener usuario del localStorage
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

  // Actualizar usuario en localStorage
  updateUser: (user: User) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  },

  // Verificar si está autenticado
  isAuthenticated: (): boolean => {
    const hasToken = !!Cookies.get(TOKEN_KEY);
    console.log('🔐 ¿Está autenticado?', hasToken);
    return hasToken;
  },

  // Cerrar sesión
  logout: () => {
    console.log('👋 Cerrando sesión...');
    Cookies.remove(TOKEN_KEY, { path: '/' });
    if (typeof window !== 'undefined') {
      localStorage.removeItem(USER_KEY);
      window.location.href = '/login';
    }
  },
};


