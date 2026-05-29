"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTaskStatus, listarArchivos, descargarArchivo, descargarTodos, descargarTodosZip, descargarTodosPorTipo } from "@/lib/api";
import type { TaskStatus, FileInfo } from "@/lib/types";

export default function TaskDetailPage() {
  const params = useParams();
  const taskId = params.id as string;

  const [task, setTask] = useState<TaskStatus | null>(null);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [filterType, setFilterType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingAll, setDownloadingAll] = useState(false);
  const [downloadingType, setDownloadingType] = useState<string | null>(null);

  const fetchTask = useCallback(async () => {
    try {
      const t = await getTaskStatus(taskId);
      setTask(t);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al obtener estado");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  const fetchFiles = useCallback(async () => {
    try {
      if (filterType) {
        const res = await descargarTodos(taskId, filterType);
        setFiles(res.archivos);
      } else {
        const res = await listarArchivos(taskId);
        setFiles(res.archivos);
      }
    } catch {
      // silencioso
    }
  }, [taskId, filterType]);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  useEffect(() => {
    if (task && task.status !== "pending") {
      fetchFiles();
    }
  }, [task, fetchFiles]);

  useEffect(() => {
    if (!task || task.status === "completed" || task.status === "failed") return;
    const interval = setInterval(fetchTask, 3000);
    return () => clearInterval(interval);
  }, [task, fetchTask]);

  const handleDownloadAllZip = async () => {
    setDownloadingAll(true);
    try {
      await descargarTodosZip(taskId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al descargar ZIP");
    } finally {
      setDownloadingAll(false);
    }
  };

  const handleDownloadByType = async (tipo: string) => {
    setDownloadingType(tipo);
    try {
      await descargarTodosPorTipo(taskId, tipo);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Error al descargar ${tipo.toUpperCase()}`);
    } finally {
      setDownloadingType(null);
    }
  };

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
    running: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    completed: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  };

  const statusLabels: Record<string, string> = {
    pending: "Pendiente",
    running: "En ejecución",
    completed: "Completado",
    failed: "Fallido",
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/tasks"
          className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          &larr; Volver
        </Link>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">
          Tarea {taskId.substring(0, 8)}...
        </h1>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {task && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Estado</div>
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[task.status] || ""}`}
              >
                {statusLabels[task.status] || task.status}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Progreso</div>
              <div className="text-lg font-semibold text-slate-900 dark:text-white">
                {task.progress}%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Descargados</div>
              <div className="text-lg font-semibold text-slate-900 dark:text-white">
                {task.descargados}/{task.total_documentos}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Pagina Actual</div>
              <div className="text-lg font-semibold text-slate-900 dark:text-white">
                {task.pagina_actual}
              </div>
            </div>
          </div>

          {task.status === "running" && (
            <div className="mb-6">
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                {task.mensaje}
              </p>
            </div>
          )}

          {task.status === "completed" && (
            <div className="mb-6">
              <div className="w-full bg-green-200 dark:bg-green-900 rounded-full h-2.5 overflow-hidden">
                <div className="bg-green-500 h-full rounded-full w-full" />
              </div>
            </div>
          )}

          <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Archivos ({files.length})
              </h2>
              <div className="flex gap-2">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  <option value="zip">ZIP</option>
                  <option value="pdf">PDF</option>
                  <option value="xml">XML</option>
                </select>
                <button
                  onClick={fetchFiles}
                  className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  Refrescar
                </button>
              </div>
            </div>

            {/* Opciones de descarga por tipo */}
            <div className="mb-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700">
              <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                📥 Descargar por tipo:
              </div>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleDownloadByType("zip")}
                  disabled={downloadingType === "zip" || !files.some(f => f.tipo?.toUpperCase() === "ZIP")}
                  className="px-3 py-2 text-sm rounded-lg bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white transition-colors font-medium"
                >
                  {downloadingType === "zip" ? "Descargando..." : "ZIP"}
                </button>
                <button
                  onClick={() => handleDownloadByType("pdf")}
                  disabled={downloadingType === "pdf" || !files.some(f => f.tipo?.toUpperCase() === "PDF")}
                  className="px-3 py-2 text-sm rounded-lg bg-red-500 hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white transition-colors font-medium"
                >
                  {downloadingType === "pdf" ? "Descargando..." : "PDF"}
                </button>
                <button
                  onClick={() => handleDownloadByType("xml")}
                  disabled={downloadingType === "xml" || !files.some(f => f.tipo?.toUpperCase() === "XML")}
                  className="px-3 py-2 text-sm rounded-lg bg-green-500 hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white transition-colors font-medium"
                >
                  {downloadingType === "xml" ? "Descargando..." : "XML"}
                </button>
              </div>
            </div>

            {files.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400 py-4 text-center">
                No hay archivos disponibles
              </p>
            ) : (
              <div className="space-y-1 max-h-96 overflow-y-auto">
                <div className="grid grid-cols-[1fr_100px_80px_80px] gap-4 px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <span>Nombre</span>
                  <span className="text-right">Tamaño</span>
                  <span className="text-center">Tipo</span>
                  <span />
                </div>
                {files.map((f) => (
                  <div
                    key={f.nombre}
                    className="grid grid-cols-[1fr_100px_80px_80px] gap-4 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-md transition-colors items-center"
                  >
                    <span className="truncate text-slate-800 dark:text-slate-200">
                      {f.nombre}
                    </span>
                    <span className="text-right text-slate-500 dark:text-slate-400">
                      {f.tamaño_kb} KB
                    </span>
                    <span className="text-center">
                      <span className="px-1.5 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono">
                        {f.tipo}
                      </span>
                    </span>
                    <button
                      onClick={() => descargarArchivo(taskId, f.nombre)}
                      className="text-xs px-2 py-1 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                    >
                      Descargar
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3">
              Detalles de la tarea
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-slate-500 dark:text-slate-400">ID: </span>
                <code className="text-slate-800 dark:text-slate-200 font-mono text-xs">
                  {task.task_id}
                </code>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Creada: </span>
                <span className="text-slate-800 dark:text-slate-200">
                  {new Date(task.created_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Actualizada: </span>
                <span className="text-slate-800 dark:text-slate-200">
                  {new Date(task.updated_at).toLocaleString()}
                </span>
              </div>
              {task.download_folder && (
                <div className="col-span-full">
                  <span className="text-slate-500 dark:text-slate-400">Carpeta: </span>
                  <code className="text-slate-800 dark:text-slate-200 font-mono text-xs">
                    {task.download_folder}
                  </code>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
