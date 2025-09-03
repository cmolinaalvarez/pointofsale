"use client";

import { useAuthContext } from "@/context/AuthContext";
import { LogOut, User, Bell, Search } from "lucide-react";

export function Header() {
  const { logout, user } = useAuthContext();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-3 relative">
      {/* Título absolutamente centrado */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <h1 className="text-xl md:text-2xl font-semibold text-gray-800 text-center whitespace-nowrap">
          Sistema de Ventas
        </h1>
      </div>

      {/* Contenido normal a la derecha */}
      <div className="flex items-center justify-end space-x-4">
        {/* Notificaciones */}
        <button className="relative p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100">
          <Bell className="w-5 h-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* Perfil de usuario */}
        <div className="flex items-center space-x-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-900">{user?.name || "Usuario"}</p>
            <p className="text-xs text-gray-500">{user?.role || "Administrador"}</p>
          </div>
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
            <User className="w-5 h-5" />
          </div>
        </div>

        {/* Botón de logout */}
        <button
          onClick={logout}
          className="p-2 text-gray-600 hover:text-red-600 rounded-lg hover:bg-gray-100 flex items-center space-x-2"
          title="Cerrar sesión"
        >
          <LogOut className="w-5 h-5" />
          <span className="hidden sm:block text-sm">Salir</span>
        </button>
      </div>
    </header>
  );
}