"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useKeys } from "../layout";
import { iniciarDescarga } from "@/lib/api";

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
      router.push(`/tasks/${res.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar la tarea");
    } finally {
      setLoading(false);
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
    </div>
  );
}
