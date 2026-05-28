"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useKeys } from "./layout";
import { getRoot, getHealth } from "@/lib/api";
import type { ServiceInfo, HealthResponse } from "@/lib/types";

export default function Dashboard() {
  const { apiKey } = useKeys();
  const [service, setService] = useState<ServiceInfo | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [svc, h] = await Promise.all([getRoot(), getHealth()]);
      setService(svc as ServiceInfo);
      setHealth(h);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo conectar al backend");
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            DIAN Document Service
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Panel de control del servicio de descarga de documentos DIAN
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-3 py-1.5 text-sm rounded-md border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          Refrescar
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="text-sm text-slate-500 dark:text-slate-400">Estado</div>
          <div className="mt-1 flex items-center gap-2">
            <span
              className={`inline-block w-2.5 h-2.5 rounded-full ${
                health?.status === "healthy" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-xl font-semibold text-slate-900 dark:text-white">
              {health?.status || "Desconectado"}
            </span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tareas Activas</div>
          <div className="mt-1 text-xl font-semibold text-slate-900 dark:text-white">
            {health?.tareas_activas ?? "-"}
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="text-sm text-slate-500 dark:text-slate-400">Versión</div>
          <div className="mt-1 text-xl font-semibold text-slate-900 dark:text-white">
            v{health?.version || "-"}
          </div>
        </div>
      </div>

      {service && (
        <div className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
            Endpoints Disponibles
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {Object.entries(service.endpoints).map(([key, value]) => (
              <div
                key={key}
                className="flex items-center justify-between p-2.5 rounded-md bg-slate-50 dark:bg-slate-700/50"
              >
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <code className="text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-mono">
                  {value}
                </code>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link
          href="/tasks"
          className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all group"
        >
          <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
            Iniciar Descarga
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Crea una nueva tarea de descarga de documentos desde la DIAN
          </p>
        </Link>

        <Link
          href="/admin"
          className="p-5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all group"
        >
          <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
            Gestionar API Keys
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Administra las API Keys del servicio (requiere Master Key)
          </p>
        </Link>
      </div>
    </div>
  );
}
