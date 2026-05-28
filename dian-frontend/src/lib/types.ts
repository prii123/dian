export interface TaskRequest {
  token_url: string;
  fecha_inicio: string;
  fecha_fin: string;
}

export interface TaskCreateResponse {
  task_id: string;
  mensaje: string;
  status: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  total_documentos: number;
  descargados: number;
  pagina_actual: number;
  mensaje: string;
  created_at: string;
  updated_at: string;
  download_folder: string | null;
}

export interface FileInfo {
  nombre: string;
  tamaño_kb: number;
  tipo: string;
}

export interface FileListResponse {
  task_id: string;
  filtro_tipo: string | null;
  archivos: FileInfo[];
  total: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  tareas_activas: number;
  version: string;
}

export interface ApiKeyCreate {
  name: string;
  description?: string;
  expires_at?: string | null;
}

export interface ApiKeyResponse {
  id: string;
  key: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  request_count: number;
}

export interface ApiKeyListResponse {
  total: number;
  keys: ApiKeyInfo[];
}

export interface ApiKeyUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface ServiceInfo {
  servicio: string;
  version: string;
  descripcion: string;
  endpoints: Record<string, string>;
}
