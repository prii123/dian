"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getLoteStatus,
  getLoteDetalles,
  reanudarLote,
  reanudarLoteConToken,
  descargarLoteComprimido,
} from "@/lib/api";
import type { LoteStatus, LoteDetalleInfo } from "@/lib/types";

export default function LoteDetailPage() {
  const params = useParams();
  const loteId = params.id as string;

  const [lote, setLote] = useState<LoteStatus | null>(null);
  const [detalles, setDetalles] = useState<LoteDetalleInfo[]>([]);
  const [totalInfo, setTotalInfo] = useState<{
    pendientes: number;
    descargados: number;
    fallidos: number;
    no_encontrados: number;
    total: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reanudando, setReanudando] = useState(false);
  const [downloadAll, setDownloadAll] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [showNewToken, setShowNewToken] = useState(false);
  const [newTokenUrl, setNewTokenUrl] = useState("");
  const [reanudandoToken, setReanudandoToken] = useState(false);

  const fetchLote = useCallback(async () => {
    try {
      const t = await getLoteStatus(loteId);
      setLote(t);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al obtener estado");
    } finally {
      setLoading(false);
    }
  }, [loteId]);

  const fetchDetalles = useCallback(async () => {
    try {
      const res = await getLoteDetalles(loteId);
      let filtered = res.detalles;
      if (filterStatus) {
        filtered = res.detalles.filter((d) => d.status === filterStatus);
      }
      setDetalles(filtered);
      setTotalInfo({
        pendientes: res.pendientes,
        descargados: res.descargados,
        fallidos: res.fallidos,
        no_encontrados: res.no_encontrados,
        total: res.total,
      });
    } catch {
      // silencioso
    }
  }, [loteId, filterStatus]);

  useEffect(() => {
    fetchLote();
  }, [fetchLote]);

  useEffect(() => {
    if (lote && lote.status !== "pending") {
      fetchDetalles();
    }
  }, [lote, fetchDetalles]);

  useEffect(() => {
    if (!lote || lote.status === "completed" || lote.status === "failed" || lote.status === "partial") return;
    const interval = setInterval(fetchLote, 3000);
    return () => clearInterval(interval);
  }, [lote, fetchLote]);

  useEffect(() => {
    if (lote) fetchDetalles();
  }, [filterStatus]);

  const handleReanudar = async () => {
    if (!confirm("Reanudar procesamiento de CUFE pendientes y fallidos?")) return;
    setReanudando(true);
    setError("");
    try {
      await reanudarLote(loteId);
      await fetchLote();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al reanudar");
    } finally {
      setReanudando(false);
    }
  };

  const handleReanudarConToken = async () => {
    if (!newTokenUrl.trim()) {
      setError("Debe ingresar el nuevo token URL de DIAN");
      return;
    }
    if (!confirm("Cargar nuevo token DIAN y reanudar procesamiento de CUFE pendientes y fallidos?")) return;
    setReanudandoToken(true);
    setError("");
    try {
      await reanudarLoteConToken(loteId, newTokenUrl.trim());
      setShowNewToken(false);
      setNewTokenUrl("");
      await fetchLote();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al reanudar con nuevo token");
    } finally {
      setReanudandoToken(false);
    }
  };

  const handleDownloadAll = async () => {
    setDownloadAll(true);
    setError("");
    try {
      await descargarLoteComprimido(loteId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al descargar");
    } finally {
      setDownloadAll(false);
    }
  };

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
    running: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    completed: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
    partial: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300",
    downloading: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
    downloaded: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    not_found: "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300",
  };

  const statusLabels: Record<string, string> = {
    pending: "Pendiente",
    running: "Procesando",
    completed: "Completado",
    failed: "Fallido",
    partial: "Parcial",
    downloading: "Descargando",
    downloaded: "Descargado",
    not_found: "No encontrado",
  };

  const canReanudar = lote && ["failed", "partial"].includes(lote.status);
  const hasDownloads = lote && lote.descargados > 0;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/lotes"
          className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          &larr; Volver
        </Link>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">
          Lote {loteId.substring(0, 8)}...
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

      {lote && (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Estado</div>
              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[lote.status] || ""}`}>
                {statusLabels[lote.status] || lote.status}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Total CUFE</div>
              <div className="text-lg font-semibold text-slate-900 dark:text-white">{lote.total_cufes}</div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Descargados</div>
              <div className="text-lg font-semibold text-green-600 dark:text-green-400">{lote.descargados}</div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Fallidos</div>
              <div className="text-lg font-semibold text-red-600 dark:text-red-400">{lote.fallidos}</div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">No encontrados</div>
              <div className="text-lg font-semibold text-slate-600 dark:text-slate-400">{lote.no_encontrados}</div>
            </div>
          </div>

          {/* Progress bar */}
          {(lote.status === "running" || lote.status === "partial") && (
            <div className="mb-6">
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${lote.progress}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">{lote.mensaje}</p>
            </div>
          )}

          {lote.status === "completed" && (
            <div className="mb-6">
              <div className="w-full bg-green-200 dark:bg-green-900 rounded-full h-2.5 overflow-hidden">
                <div className="bg-green-500 h-full rounded-full w-full" />
              </div>
            </div>
          )}

           {/* Action buttons */}
          <div className="flex gap-3 mb-6">
            {canReanudar && (
              <>
                <button
                  onClick={handleReanudar}
                  disabled={reanudando}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white text-sm font-medium transition-colors"
                >
                  {reanudando ? "Reanudando..." : "Reanudar Lote"}
                </button>
                <button
                  onClick={() => setShowNewToken(true)}
                  disabled={reanudando}
                  className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium transition-colors"
                >
                  Cargar nuevo token DIAN y reanudar
                </button>
              </>
            )}
            {hasDownloads && (
              <button
                onClick={handleDownloadAll}
                disabled={downloadAll}
                className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                {downloadAll ? "Descargando..." : `Descargar Todo (.zip) - ${lote.descargados} archivos`}
              </button>
            )}
          </div>

          {/* Modal para nuevo token */}
          {showNewToken && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4 border border-slate-200 dark:border-slate-700">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                  Cargar nuevo token DIAN
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                  Ingresa la nueva URL completa con el token de autenticacion de DIAN.
                  Se reanudara el procesamiento con los CUFE pendientes y fallidos guardados.
                </p>
                <textarea
                  value={newTokenUrl}
                  onChange={(e) => setNewTokenUrl(e.target.value)}
                  placeholder="https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&amp;rk=yyy&amp;token=zzz"
                  className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-red-500 resize-none"
                  rows={3}
                />
                <div className="flex gap-3 justify-end mt-4">
                  <button
                    onClick={() => { setShowNewToken(false); setNewTokenUrl(""); }}
                    disabled={reanudandoToken}
                    className="px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 disabled:opacity-50 text-sm font-medium transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleReanudarConToken}
                    disabled={reanudandoToken}
                    className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium transition-colors"
                  >
                    {reanudandoToken ? "Reanudando..." : "Cargar token y reanudar"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* CUFE details table */}
          <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Detalle CUFE ({detalles.length}{totalInfo ? `/${totalInfo.total}` : ""})
              </h2>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  <option value="pending">Pendientes</option>
                  <option value="downloaded">Descargados</option>
                  <option value="failed">Fallidos</option>
                  <option value="not_found">No encontrados</option>
                  <option value="downloading">Descargando</option>
                </select>
                <button
                  onClick={fetchDetalles}
                  className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  Refrescar
                </button>
              </div>
            </div>

            {detalles.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400 py-4 text-center">
                {lote.status === "pending" ? "Esperando inicio del procesamiento..." : "Sin resultados"}
              </p>
            ) : (
              <div className="space-y-1 max-h-[600px] overflow-y-auto">
                <div className="grid grid-cols-[1fr_100px_80px_100px] gap-4 px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <span>CUFE</span>
                  <span className="text-center">Estado</span>
                  <span className="text-center">Intentos</span>
                  <span className="text-right">Ultimo intento</span>
                </div>
                {detalles.map((d) => (
                  <div
                    key={d.id}
                    className="grid grid-cols-[1fr_100px_80px_100px] gap-4 px-3 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-md transition-colors items-center"
                  >
                    <div className="min-w-0">
                      <code className="text-xs text-slate-800 dark:text-slate-200 break-all">{d.cufe}</code>
                      {d.mensaje && (
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 truncate">{d.mensaje}</p>
                      )}
                    </div>
                    <span className="text-center">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${statusColors[d.status] || ""}`}>
                        {statusLabels[d.status] || d.status}
                      </span>
                    </span>
                    <span className="text-center text-slate-500 dark:text-slate-400 text-xs">
                      {d.intentos}
                    </span>
                    <span className="text-right text-slate-500 dark:text-slate-400 text-xs">
                      {d.ultimo_intento ? new Date(d.ultimo_intento).toLocaleString() : "-"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Lote info */}
          <div className="mt-6 p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3">
              Detalles del lote
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-slate-500 dark:text-slate-400">ID: </span>
                <code className="text-slate-800 dark:text-slate-200 font-mono text-xs">{lote.lote_id}</code>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Archivo: </span>
                <span className="text-slate-800 dark:text-slate-200">{lote.filename}</span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Creado: </span>
                <span className="text-slate-800 dark:text-slate-200">{new Date(lote.created_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">Actualizado: </span>
                <span className="text-slate-800 dark:text-slate-200">{new Date(lote.updated_at).toLocaleString()}</span>
              </div>
              {lote.completed_at && (
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Completado: </span>
                  <span className="text-slate-800 dark:text-slate-200">{new Date(lote.completed_at).toLocaleString()}</span>
                </div>
              )}
              {lote.download_folder && (
                <div className="col-span-full">
                  <span className="text-slate-500 dark:text-slate-400">Carpeta: </span>
                  <code className="text-slate-800 dark:text-slate-200 font-mono text-xs">{lote.download_folder}</code>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
