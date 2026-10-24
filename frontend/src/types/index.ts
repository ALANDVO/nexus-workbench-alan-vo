export type UserRole = 'viewer' | 'operator' | 'admin';

export interface User {
  id: number;
  sub: string;
  email: string | null;
  username: string;
  role: UserRole;
}

export interface AuthConfig {
  keycloak_url: string;
  realm: string;
  client_id: string;
  redirect_uri: string;
  authenticated: boolean;
  user: User | null;
}

export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export type AnalysisType =
  | 'vtable_resolution'
  | 'switch_recovery'
  | 'jmp_call_recovery'
  | 'string_recovery'
  | 'batch_decompilation';

export interface Analysis {
  id: number;
  name: string;
  description: string | null;
  analysis_type: AnalysisType;
  status: AnalysisStatus;
  input_data: string | null;
  result_data: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  user_id: number;
}

export interface AnalysisListResponse {
  items: Analysis[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnalysisCreate {
  name: string;
  description?: string;
  analysis_type: AnalysisType;
  input_data?: string;
}

export interface AnalysisUpdate {
  name?: string;
  description?: string;
  status?: AnalysisStatus;
  result_data?: string;
  error_message?: string;
}

export interface AnalysisRunResponse {
  analysis_id: number;
  status: AnalysisStatus;
  functions_count: number;
  vtables_count: number;
  switches_count: number;
  jmp_calls_count: number;
  strings_count: number;
  cross_references_count: number;
}
