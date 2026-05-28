"use client";

import { useState, useEffect, createContext, useContext } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { setApiKey, setMasterApiKey, clearKeys } from "@/lib/api";
import "./globals.css";

interface KeysContextType {
  apiKey: string;
  masterKey: string;
  setApiKeyCtx: (k: string) => void;
  setMasterKeyCtx: (k: string) => void;
}

const KeysContext = createContext<KeysContextType>({
  apiKey: "",
  masterKey: "",
  setApiKeyCtx: () => {},
  setMasterKeyCtx: () => {},
});

export const useKeys = () => useContext(KeysContext);

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKeyState] = useState("");
  const [masterKey, setMasterKeyState] = useState("");
  const [showKeys, setShowKeys] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setApiKeyState(localStorage.getItem("dian_api_key") || "");
    setMasterKeyState(localStorage.getItem("dian_master_api_key") || "");
  }, []);

  const handleSetApiKey = (k: string) => {
    setApiKeyState(k);
    setApiKey(k);
  };

  const handleSetMasterKey = (k: string) => {
    setMasterKeyState(k);
    setMasterApiKey(k);
  };

  const handleClear = () => {
    setApiKeyState("");
    setMasterKeyState("");
    clearKeys();
  };

  const navItems = [
    { href: "/", label: "Dashboard" },
    { href: "/tasks", label: "Tareas" },
    { href: "/admin", label: "API Keys" },
  ];

  return (
    <html lang="es" className="h-full">
      <body className="min-h-full flex flex-col">
        <KeysContext.Provider
          value={{
            apiKey,
            masterKey,
            setApiKeyCtx: handleSetApiKey,
            setMasterKeyCtx: handleSetMasterKey,
          }}
        >
          <header className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="max-w-7xl mx-auto px-4">
              <div className="flex items-center justify-between h-14">
                <div className="flex items-center gap-6">
                  <Link href="/" className="font-bold text-lg text-blue-600 dark:text-blue-400">
                    DIAN Service
                  </Link>
                  <nav className="flex gap-1">
                    {navItems.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                          pathname === item.href
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800"
                        }`}
                      >
                        {item.label}
                      </Link>
                    ))}
                  </nav>
                </div>
                <div className="flex items-center gap-2">
                  {apiKey && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                      API Key configurada
                    </span>
                  )}
                  <button
                    onClick={() => setShowKeys(!showKeys)}
                    className="px-3 py-1.5 text-xs rounded-md border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    {showKeys ? "Ocultar Keys" : "Configurar Keys"}
                  </button>
                </div>
              </div>
              {showKeys && (
                <div className="py-3 border-t border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row gap-3">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                      API Key (X-API-Key)
                    </label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => handleSetApiKey(e.target.value)}
                      placeholder="Ingresa tu API Key..."
                      className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                      Master Key (Admin)
                    </label>
                    <input
                      type="password"
                      value={masterKey}
                      onChange={(e) => handleSetMasterKey(e.target.value)}
                      placeholder="Ingresa la Master Key..."
                      className="w-full px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleClear}
                      className="px-3 py-1.5 text-xs rounded-md bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/30 transition-colors"
                    >
                      Limpiar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </KeysContext.Provider>
      </body>
    </html>
  );
}
