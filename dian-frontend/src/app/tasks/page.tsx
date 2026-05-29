"use client";

import { useState, FormEvent, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useKeys } from "../layout";
import { iniciarDescarga, getMyTasks } from "@/lib/api";
import type { TaskStatus } from "@/lib/types";

export default function TasksPage() {
  const router = useRouter();
  const { apiKey } = useKeys();
  const [form, setForm] = useState({
    token_url: "",
    fecha_inicio: "",
    fecha_fin: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [myTasks, setMyTasks] = useState<TaskStatus[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  // Cargar mis tareas
  const fetchMyTasks = async () => {
    if (!apiKey) return;
    setLoadingTasks(true);
    try {
      const res = await getMyTasks();
      setMyTasks(res.tareas);
    } catch (err) {
      console.error("Error loading tasks:", err);
    } finally {
      setLoadingTasks(false);
    }
  };

  useEffect(() => {
    fetchMyTasks();
    const interval = setInterval(fetchMyTasks, 10000); // Recargar cada 10 segundos
    return () => clearInterval(interval);
  }, [apiKey]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!apiKey) {
      setError("Configura tu API Key en la barra superior primero.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await iniciarDescarga(form);
      setSuccess(`Tarea ${res.task_id} iniciada`);
      setForm({ token_url: "", fecha_inicio: "", fecha_fin: "" });
      await fetchMyTasks();
      router.push(`/tasks/${res.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar la tarea");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
      case "running":
        return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
      case "failed":
        return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
      case "pending":
        return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300";
      default:
        return "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300";
    }
  };

  const today = new Date();
  const dd = String(today.getDate()).padStart(2, "0");
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const yyyy = today.getFullYear();

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
        Iniciar Descarga DIAN
      </h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8">
        Configura los parámetros para iniciar una descarga automatizada de documentos
      </p>

      {!apiKey && (
        <div className="mb-6 p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 text-sm">
          Configura tu API Key en la barra superior antes de iniciar una descarga.
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 text-sm">
          {success}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-5"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Token URL
          </label>
          <input
            type="url"
            required
            value={form.token_url}
            onChange={(e) => setForm({ ...form, token_url: e.target.value })}
            placeholder="https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz"
            className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Fecha Inicio
            </label>
            <input
              type="text"
              required
              pattern="\d{2}-\d{2}-\d{4}"
              value={form.fecha_inicio}
              onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })}
              placeholder={`${dd}-${mm}-${yyyy}`}
              className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <p className="text-xs text-slate-400 mt-1">Formato: DD-MM-YYYY</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Fecha Fin
            </label>
            <input
              type="text"
              required
              pattern="\d{2}-\d{2}-\d{4}"
              value={form.fecha_fin}
              onChange={(e) => setForm({ ...form, fecha_fin: e.target.value })}
              placeholder={`${dd}-${mm}-${yyyy}`}
              className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <p className="text-xs text-slate-400 mt-1">Formato: DD-MM-YYYY</p>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !apiKey}
          className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Iniciando...
            </span>
          ) : (
            "Iniciar Descarga"
          )}
        </button>
      </form>

      {/* Mis tareas */}
      <div className="mt-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Mis Tareas ({myTasks.length})
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {apiKey ? "Tareas asociadas a tu API Key" : "Configura tu API Key para ver tus tareas"}
            </p>
          </div>
          <button
            onClick={fetchMyTasks}
            disabled={loadingTasks}
            className="px-3 py-1.5 text-sm rounded-md border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition-colors"
          >
            {loadingTasks ? "Cargando..." : "Actualizar"}
          </button>
        </div>

        {myTasks.length === 0 ? (
          <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-center">
            <p className="text-slate-500 dark:text-slate-400">
              {apiKey ? "No hay tareas aún. Crea una para empezar." : "Inicia sesión para ver tus tareas."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {myTasks.map((task) => (
              <Link
                key={task.task_id}
                href={`/tasks/${task.task_id}`}
                className="block p-4 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {new Date(task.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-900 dark:text-white font-medium truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {task.fecha_inicio} - {task.fecha_fin}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
                      ID: {task.task_id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">
                        {task.descargados}/{task.total_documentos}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {task.progress.toFixed(0)}%
                      </p>
                    </div>
                    {task.status === "running" && (
                      <div className="w-16 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
