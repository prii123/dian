"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useKeys } from "../layout";
import { uploadLote, getLotes } from "@/lib/api";
import type { LoteStatus } from "@/lib/types";

export default function LotesPage() {
  const router = useRouter();
  const { apiKey } = useKeys();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tokenUrl, setTokenUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [lotes, setLotes] = useState<LoteStatus[]>([]);
  const [loadingLotes, setLoadingLotes] = useState(false);

  const fetchLotes = async () => {
    if (!apiKey) return;
    setLoadingLotes(true);
    try {
      const res = await getLotes();
      setLotes(res.lotes);
    } catch {
      // silencioso
    } finally {
      setLoadingLotes(false);
    }
  };

  useEffect(() => {
    fetchLotes();
    const interval = setInterval(fetchLotes, 10000);
    return () => clearInterval(interval);
  }, [apiKey]);

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!apiKey) {
      setError("Configura tu API Key primero.");
      return;
    }
    if (!selectedFile) {
      setError("Selecciona un archivo Excel.");
      return;
    }
    if (!tokenUrl) {
      setError("Ingresa el Token URL.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await uploadLote(selectedFile, tokenUrl);
      setSuccess(`Lote ${res.lote_id.slice(0, 8)}... creado con ${res.total_cufes} CUFE`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchLotes();
      router.push(`/lotes/${res.lote_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir lote");
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
      case "partial":
        return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300";
      case "pending":
        return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300";
      default:
        return "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "pending": return "Pendiente";
      case "running": return "Procesando";
      case "completed": return "Completado";
      case "failed": return "Fallido";
      case "partial": return "Parcial";
      default: return status;
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
        Lotes por CUFE
      </h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8">
        Sube un archivo Excel con columna de CUFE para descargar documentos especificos de la DIAN
      </p>

      {!apiKey && (
        <div className="mb-6 p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 text-sm">
          Configura tu API Key en la barra superior antes de iniciar.
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
        onSubmit={handleUpload}
        className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-5"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Archivo Excel (.xlsx)
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            required
            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900/20 dark:file:text-blue-300 dark:hover:file:bg-blue-900/30 text-slate-500 dark:text-slate-400"
          />
        <p className="text-xs text-slate-400 mt-1">
            La busqueda se hace directamente por CUFE en el portal DIAN sin necesidad de rango de fechas.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Token URL
          </label>
          <input
            type="url"
            required
            value={tokenUrl}
            onChange={(e) => setTokenUrl(e.target.value)}
            placeholder="https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz"
            className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !apiKey}
          className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Subiendo...
            </span>
          ) : (
            "Subir y Procesar Lote"
          )}
        </button>
      </form>

      {/* Lista de lotes */}
      <div className="mt-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Mis Lotes ({lotes.length})
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {apiKey ? "Lotes asociados a tu API Key" : "Configura tu API Key para ver tus lotes"}
            </p>
          </div>
          <button
            onClick={fetchLotes}
            disabled={loadingLotes}
            className="px-3 py-1.5 text-sm rounded-md border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition-colors"
          >
            {loadingLotes ? "Cargando..." : "Actualizar"}
          </button>
        </div>

        {lotes.length === 0 ? (
          <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-center">
            <p className="text-slate-500 dark:text-slate-400">
              {apiKey ? "No hay lotes aun. Sube un Excel para empezar." : "Configura tu API Key para ver tus lotes."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {lotes.map((lote) => (
              <Link
                key={lote.lote_id}
                href={`/lotes/${lote.lote_id}`}
                className="block p-4 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lote.status)}`}>
                        {getStatusLabel(lote.status)}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {new Date(lote.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-900 dark:text-white font-medium truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {lote.filename}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {lote.descargados} descargados / {lote.fallidos} fallidos / {lote.no_encontrados} no encontrados
                    </p>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 truncate">
                      ID: {lote.lote_id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">
                        {lote.descargados}/{lote.total_cufes}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {lote.progress.toFixed(0)}%
                      </p>
                    </div>
                    {lote.status === "running" && (
                      <div className="w-16 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all"
                          style={{ width: `${lote.progress}%` }}
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
