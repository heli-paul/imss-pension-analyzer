// src/frontend/lib/api.ts
import axios from 'axios';
import Cookies from 'js-cookie';
import type { AuthResponse, LoginCredentials, RegisterData, User, AnalysisResult, DashboardStats } from '@/types';

// URL base del backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

console.log('🔧 API URL configurada:', API_URL);

// Crear instancia de axios
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a todas las peticiones
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Token COMPLETO:', token);
    } else {
      console.warn('⚠️ No hay token disponible para la petición');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => {
    console.log('✅ Respuesta exitosa:', response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ Error en petición:', error.config?.url, error.response?.status);
    
    if (error.response?.status === 401) {
      console.warn('🔒 Token inválido o expirado - limpiando sesión');
      Cookies.remove('token', { path: '/' });
      if (typeof window !== 'undefined') {
        localStorage.removeItem('user');
        
        // Solo redirigir si no estamos ya en login
        if (!window.location.pathname.includes('/login') && 
            !window.location.pathname.includes('/register')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      console.log('🔐 Intentando login...');
      console.log('📧 Email:', credentials.email);
      
      // Usar /auth/login con form-data (OAuth2PasswordRequestForm)
      const formData = new FormData();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);
      
      const response = await axios.post(
        `${API_URL}/auth/login`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      console.log('✅ Login exitoso (form-data)');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error en login:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    try {
      console.log('📝 Intentando registro...');
      console.log('📧 Email:', data.email);
      
      const response = await axios.post(`${API_URL}/auth/register`, data, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log('✅ Registro exitoso');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error en registro:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  },

  getCurrentUser: async (): Promise<User> => {
    console.log('👤 Obteniendo usuario actual...');
    const response = await api.get('/auth/me');
    console.log('✅ Usuario obtenido:', response.data.email);
    return response.data;
  },
};

// Analysis API
export const analysisAPI = {
  uploadFile: async (file: File): Promise<AnalysisResult> => {
    try {
      console.log('📤 Subiendo archivo:', file.name);
      console.log('📏 Tamaño:', (file.size / 1024).toFixed(2), 'KB');
      console.log('🔑 Token actual:', Cookies.get('token') ? 'Presente' : 'AUSENTE');
      
      const formData = new FormData();
      formData.append('pdf', file);

      // El endpoint correcto es /analysis/analizar
      const response = await api.post('/analysis/analizar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('✅ Archivo subido exitosamente');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error subiendo archivo:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        hasToken: !!Cookies.get('token')
      });
      throw error;
    }
  },

  getAnalysis: async (id: number): Promise<AnalysisResult> => {
    const response = await api.get(`/analysis/${id}`);
    return response.data;
  },

  listAnalyses: async (skip = 0, limit = 20): Promise<AnalysisResult[]> => {
    const response = await api.get('/analysis/list', {
      params: { skip, limit },
    });
    return response.data;
  },

  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/analysis/dashboard');
    return response.data;
  },

  deleteAnalysis: async (id: number): Promise<void> => {
    await api.delete(`/analysis/${id}`);
  },
};

export default api;


