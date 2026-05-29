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
  fecha_inicio?: string;
  fecha_fin?: string;
}

export interface TaskListResponse {
  total: number;
  tareas: TaskStatus[];
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

// =====================================================
// Lotes (procesamiento por CUFE)
// =====================================================

export interface LoteUploadResponse {
  lote_id: string;
  filename: string;
  total_cufes: number;
  mensaje: string;
  status: string;
}

export interface LoteStatus {
  lote_id: string;
  filename: string;
  status: string;
  total_cufes: number;
  descargados: number;
  fallidos: number;
  no_encontrados: number;
  progress: number;
  mensaje: string | null;
  download_folder: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface LoteListResponse {
  total: number;
  lotes: LoteStatus[];
}

export interface LoteDetalleInfo {
  id: string;
  cufe: string;
  status: string;
  download_path: string | null;
  mensaje: string | null;
  intentos: number;
  ultimo_intento: string | null;
}

export interface LoteDetalleListResponse {
  lote_id: string;
  detalles: LoteDetalleInfo[];
  total: number;
  pendientes: number;
  descargados: number;
  fallidos: number;
  no_encontrados: number;
}
