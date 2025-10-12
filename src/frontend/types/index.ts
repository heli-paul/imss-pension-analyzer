// types/index.ts

export interface User {
  id: number;
  email: string;
  plan: 'free' | 'premium';
  analyses_used: number;
  analyses_limit: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AnalysisResult {
  id: number;
  user_id: number;
  filename: string;
  created_at: string;
  status: 'processing' | 'completed' | 'error';
  result?: {
    informacion_trabajador: {
      nss: string;
      curp: string;
      nombre: string;
      fecha_nacimiento: string;
      sexo: string;
    };
    historial_laboral: Array<{
      patron: string;
      registro_patronal: string;
      fecha_inicio: string;
      fecha_fin: string;
      semanas_cotizadas: number;
      salario_base: number;
      salario_diario_integrado: number;
    }>;
    resumen: {
      total_semanas: number;
      semanas_descontadas_empalmes: number;
      semanas_netas: number;
      promedio_salarial_250: number;
      conservacion_derechos: {
        tiene_derecho: boolean;
        semanas_requeridas: number;
        semanas_disponibles: number;
        fecha_inicio_periodo: string;
        fecha_fin_periodo: string;
      };
    };
    empalmes?: Array<{
      patron1: string;
      patron2: string;
      fecha_inicio: string;
      fecha_fin: string;
      semanas_empalme: number;
    }>;
  };
}

export interface DashboardStats {
  total_analyses: number;
  analyses_used: number;
  analyses_limit: number;
  recent_analyses: AnalysisResult[];
}
