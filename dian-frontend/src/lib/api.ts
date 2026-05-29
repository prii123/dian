const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getApiKey(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("dian_api_key") || "";
  }
  return "";
}

function getMasterApiKey(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("dian_master_api_key") || "";
  }
  return "";
}

export function setApiKey(key: string) {
  localStorage.setItem("dian_api_key", key);
}

export function setMasterApiKey(key: string) {
  localStorage.setItem("dian_master_api_key", key);
}

export function clearKeys() {
  localStorage.removeItem("dian_api_key");
  localStorage.removeItem("dian_master_api_key");
}

function extractError(body: unknown, status: number): string {
  if (!body || typeof body !== "object") return `Error ${status}`;
  const obj = body as Record<string, unknown>;
  const detail = obj.detail;
  if (Array.isArray(detail)) {
    return (detail as Array<{ msg?: string }>)
      .map((e) => e.msg)
      .filter(Boolean)
      .join("; ") || `Error ${status}`;
  }
  if (typeof detail === "string") return detail;
  if (typeof obj.message === "string") return obj.message;
  return `Error ${status}`;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  useMaster = false
): Promise<T> {
  const key = useMaster ? getMasterApiKey() : getApiKey();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (key) {
    headers["X-API-Key"] = key;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractError(body, res.status));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export function apiDownloadUrl(path: string): string {
  const key = getApiKey();
  return `${API_BASE}${path}`;
}

export async function downloadWithAuth(path: string, filename: string) {
  const key = getApiKey();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: key ? { "X-API-Key": key } : {},
  });

  if (!res.ok) throw new Error("Error al descargar");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Health
export function getRoot() {
  return apiFetch<{ servicio: string; version: string; endpoints: Record<string, string> }>("/");
}

export function getHealth() {
  return apiFetch<import("./types").HealthResponse>("/health");
}

// Tasks
export function iniciarDescarga(data: import("./types").TaskRequest) {
  return apiFetch<import("./types").TaskCreateResponse>("/api/iniciar-descarga", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getTaskStatus(taskId: string) {
  return apiFetch<import("./types").TaskStatus>(`/api/estado-tarea/${taskId}`);
}

export function getMyTasks() {
  return apiFetch<import("./types").TaskListResponse>(`/api/mis-tareas`);
}

// Files
export function listarArchivos(taskId: string) {
  return apiFetch<{ task_id: string; archivos: import("./types").FileInfo[]; total: number }>(
    `/api/listar-archivos/${taskId}`
  );
}

export function descargarArchivo(taskId: string, nombre: string) {
  return downloadWithAuth(`/api/descargar-archivo/${taskId}/${nombre}`, nombre);
}

export function descargarTodos(taskId: string, tipo?: string) {
  const params = tipo ? `?tipo=${tipo}` : "";
  return apiFetch<import("./types").FileListResponse>(
    `/api/descargar-todos/${taskId}${params}`
  );
}

export async function descargarTodosPorTipo(taskId: string, tipo: string) {
  const key = getApiKey();
  const res = await fetch(
    `${API_BASE}/api/descargar-todos-comprimido/${taskId}?tipo=${tipo}`,
    {
      headers: key ? { "X-API-Key": key } : {},
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractError(body, res.status));
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  // Obtener nombre del archivo del header Content-Disposition
  const contentDisposition = res.headers.get("Content-Disposition");
  let filename = `documentos_${tipo}.zip`;

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename=(.+)/);
    if (filenameMatch) {
      filename = filenameMatch[1].replace(/"/g, "");
    }
  }

  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function descargarTodosZip(taskId: string) {
  await descargarTodosPorTipo(taskId, "zip");
}

// Admin API Keys
export function createApiKey(data: import("./types").ApiKeyCreate) {
  return apiFetch<import("./types").ApiKeyResponse>(
    "/admin/api-keys",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
    true
  );
}

export function listApiKeys() {
  return apiFetch<import("./types").ApiKeyListResponse>("/admin/api-keys", {}, true);
}

export function getApiKeyDetail(id: string) {
  return apiFetch<import("./types").ApiKeyInfo>(`/admin/api-keys/${id}`, {}, true);
}

export function updateApiKey(id: string, data: import("./types").ApiKeyUpdate) {
  return apiFetch<import("./types").ApiKeyInfo>(
    `/admin/api-keys/${id}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
    true
  );
}

export function revokeApiKey(id: string) {
  return apiFetch<void>(
    `/admin/api-keys/${id}`,
    { method: "DELETE" },
    true
  );
}

// Lotes CUFE
export async function uploadLote(
  file: File,
  token_url: string,
  fecha_inicio?: string,
  fecha_fin?: string,
  columna?: string
) {
  const key = getApiKey();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("token_url", token_url);
  if (fecha_inicio) formData.append("fecha_inicio", fecha_inicio);
  if (fecha_fin) formData.append("fecha_fin", fecha_fin);
  if (columna) formData.append("columna", columna);

  const res = await fetch(`${API_BASE}/api/lotes/upload`, {
    method: "POST",
    headers: key ? { "X-API-Key": key } : {},
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractError(body, res.status));
  }

  return res.json() as Promise<import("./types").LoteUploadResponse>;
}

export function getLotes() {
  return apiFetch<import("./types").LoteListResponse>("/api/lotes");
}

export function getLoteStatus(loteId: string) {
  return apiFetch<import("./types").LoteStatus>(`/api/lotes/${loteId}`);
}

export function getLoteDetalles(loteId: string) {
  return apiFetch<import("./types").LoteDetalleListResponse>(
    `/api/lotes/${loteId}/detalles`
  );
}

export async function reanudarLote(loteId: string) {
  return apiFetch<import("./types").LoteStatus>(`/api/lotes/${loteId}/reanudar`, {
    method: "POST",
  });
}

export async function reanudarLoteConToken(loteId: string, token_url: string) {
  return apiFetch<import("./types").LoteStatus>(`/api/lotes/${loteId}/reanudar-con-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token_url }),
  });
}

export async function descargarLoteComprimido(loteId: string) {
  const key = getApiKey();
  const res = await fetch(`${API_BASE}/api/lotes/${loteId}/descargar-comprimido`, {
    headers: key ? { "X-API-Key": key } : {},
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractError(body, res.status));
  }

  const blob = await res.blob();
  const contentDisposition = res.headers.get("Content-Disposition");
  let filename = `lote_${loteId.slice(0, 8)}.zip`;
  if (contentDisposition) {
    const m = contentDisposition.match(/filename=(.+)/);
    if (m) filename = m[1].replace(/"/g, "");
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
