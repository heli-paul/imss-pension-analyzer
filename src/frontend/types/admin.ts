// types/admin.ts
export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_credits_distributed: number;
  pending_invitations: number;
}

export interface User {
  id: number;
  email: string;
  full_name?: string;
  credits: number;
  credits_expire_at: string | null;
  company_size: string | null;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  is_admin?: boolean;
}

export interface Invitation {
  id: number;
  email: string;
  token: string;
  initial_credits: number;
  credits_valid_days: number;
  used: boolean;
  created_at: string;
  used_at?: string | null;
  registered_user_id?: number | null;
}

export interface InvitationCreateRequest {
  email: string;
  initial_credits: number;
  credits_valid_days: number;
}

export interface AddCreditsRequest {
  user_id: number;
  credits: number;
  valid_days: number;
}

export const COMPANY_SIZE_OPTIONS = [
  { value: '1-5', label: '1-5 empleados' },
  { value: '5-10', label: '5-10 empleados' },
  { value: '10-30', label: '10-30 empleados' },
  { value: '30-50', label: '30-50 empleados' },
  { value: '50-100', label: '50-100 empleados' },
  { value: '100+', label: 'Más de 100 empleados' },
] as const;
