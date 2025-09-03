"use client";
import type React from "react";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { useAuthContext } from "@/context/AuthContext";
import LoginPage from "@/app/login/page";
import { DashboardCharts } from "@/components/dashboard-charts";

export default function AppContentClient({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthContext();
  const router = useRouter();
  const pathname = usePathname();
  
  // Redirección automática al login si no está autenticado y no está ya en /login
  useEffect(() => {
    if (!isLoading && !isAuthenticated && pathname !== "/login") {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Detecta si es pantalla pequeña
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Mostrar pantalla de carga inicial
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  // Si no está autenticado, mostrar solo la página de login
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100 relative">
        {/* Fondo decorativo */}
        <div className="absolute inset-0 w-full h-full flex items-center justify-center pointer-events-none select-none transition-all duration-700 opacity-50 blur-md scale-105 animate-fadein z-10">
          <DashboardCharts />
        </div>
        {/* Login centrado */}
        <div className="relative z-20 w-full flex items-center justify-center">
          <LoginPage />
        </div>
        <style>{`
          @keyframes fadein {
            0% { opacity: 0; transform: scale(1); }
            100% { opacity: 0.5; transform: scale(1.05); }
          }
          .animate-fadein {
            animation: fadein 1s ease-in;
          }
        `}</style>
      </div>
    );
  }

  // Si está autenticado, mostrar la estructura completa de la aplicación
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar responsivo - solo en desktop se muestra fijo */}
      {!isMobile && (
        <div className="hidden md:block">
          <Sidebar />
        </div>
      )}
      
      {/* Sidebar móvil - manejado internamente por el componente Sidebar */}
      {isMobile && <Sidebar />}
      
      {/* Contenido principal */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-2 sm:p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}