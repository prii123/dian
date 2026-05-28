"use client";

import { useEffect, useState, FormEvent, useCallback } from "react";
import { useKeys } from "../layout";
import {
  listApiKeys,
  createApiKey,
  updateApiKey,
  revokeApiKey,
} from "@/lib/api";
import type { ApiKeyInfo, ApiKeyResponse } from "@/lib/types";

export default function AdminPage() {
  const { masterKey } = useKeys();
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState({ name: "", description: "" });
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyResponse | null>(null);

  const fetchKeys = useCallback(async () => {
    if (!masterKey) return;
    try {
      const res = await listApiKeys();
      setKeys(res.keys);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al listar API Keys");
    } finally {
      setLoading(false);
    }
  }, [masterKey]);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    setSuccess("");
    try {
      const res = await createApiKey(newKey);
      setCreatedKey(res);
      setSuccess("API Key creada exitosamente");
      setShowCreate(false);
      setNewKey({ name: "", description: "" });
      fetchKeys();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear API Key");
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (id: string, currentActive: boolean) => {
    try {
      await updateApiKey(id, { is_active: !currentActive });
      setSuccess(currentActive ? "API Key desactivada" : "API Key activada");
      fetchKeys();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al actualizar");
    }
  };

  const handleRevoke = async (id: string) => {
    if (!confirm("¿Estás seguro de desactivar esta API Key?")) return;
    try {
      await revokeApiKey(id);
      setSuccess("API Key revocada");
      fetchKeys();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al revocar");
    }
  };

  if (!masterKey) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="p-6 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <h2 className="font-semibold text-amber-800 dark:text-amber-300 mb-1">
            Master Key requerida
          </h2>
          <p className="text-sm text-amber-700 dark:text-amber-400">
            Configura la Master Key en la barra de navegación superior para acceder a la
            administración de API Keys.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Administración de API Keys
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Gestiona las claves de acceso al servicio
          </p>
        </div>
        <button
          onClick={() => {
            setShowCreate(!showCreate);
            setCreatedKey(null);
          }}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          {showCreate ? "Cancelar" : "Nueva API Key"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 text-sm">
          {success}
        </div>
      )}

      {createdKey && (
        <div className="mb-6 p-5 rounded-xl bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-400 dark:border-amber-600">
          <h3 className="font-bold text-amber-800 dark:text-amber-300 mb-2">
            API Key Creada - ¡Guárdala ahora!
          </h3>
          <p className="text-xs text-amber-700 dark:text-amber-400 mb-2">
            Esta clave solo se muestra una vez. Copiala y guardala en un lugar seguro.
          </p>
          <code className="block p-3 rounded-md bg-white dark:bg-slate-800 border border-amber-200 dark:border-amber-700 text-sm font-mono break-all select-all">
            {createdKey.key}
          </code>
          <button
            onClick={() => {
              navigator.clipboard.writeText(createdKey.key);
              setSuccess("API Key copiada al portapapeles");
            }}
            className="mt-2 px-3 py-1 text-xs rounded bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 hover:bg-amber-300 dark:hover:bg-amber-700 transition-colors"
          >
            Copiar
          </button>
        </div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-4"
        >
          <h2 className="font-semibold text-slate-900 dark:text-white">Nueva API Key</h2>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Nombre *
            </label>
            <input
              type="text"
              required
              minLength={3}
              value={newKey.name}
              onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
              placeholder="Cliente ABC Corp"
              className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Descripción
            </label>
            <input
              type="text"
              value={newKey.description}
              onChange={(e) => setNewKey({ ...newKey, description: e.target.value })}
              placeholder="API key para proyecto X"
              className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {creating ? "Creando..." : "Crear API Key"}
          </button>
        </form>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      ) : (
        <div className="rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          <div className="grid grid-cols-[1fr_100px_100px_120px_80px] gap-4 px-5 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
            <span>Nombre</span>
            <span className="text-center">Estado</span>
            <span className="text-center">Peticiones</span>
            <span className="text-center">Ultimo uso</span>
            <span />
          </div>
          {keys.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
              No hay API Keys registradas
            </p>
          ) : (
            keys.map((k) => (
              <div
                key={k.id}
                className="grid grid-cols-[1fr_100px_100px_120px_80px] gap-4 px-5 py-3 text-sm border-b border-slate-100 dark:border-slate-700/50 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors items-center"
              >
                <div>
                  <div className="font-medium text-slate-900 dark:text-white">{k.name}</div>
                  {k.description && (
                    <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                      {k.description}
                    </div>
                  )}
                </div>
                <div className="text-center">
                  <button
                    onClick={() => handleToggleActive(k.id, k.is_active)}
                    className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                      k.is_active
                        ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 hover:bg-green-200"
                        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 hover:bg-red-200"
                    }`}
                  >
                    {k.is_active ? "Activa" : "Inactiva"}
                  </button>
                </div>
                <div className="text-center text-slate-500 dark:text-slate-400">
                  {k.request_count}
                </div>
                <div className="text-center text-xs text-slate-500 dark:text-slate-400">
                  {k.last_used_at
                    ? new Date(k.last_used_at).toLocaleDateString()
                    : "Nunca"}
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => handleRevoke(k.id)}
                    className="px-2 py-1 text-xs rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 transition-colors"
                  >
                    Revocar
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
