"use client";
import { useAuth } from "@/hooks/useAuth";
import POSInterface from "@/components/pos-interface";

export default function CreateSale() {
  const { token } = useAuth();

  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <span className="text-lg font-semibold">Acceso restringido. Inicia sesión para crear una venta.</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Crear Venta</h1>
        <p className="text-gray-600">Sistema de punto de venta</p>
      </div>

      <POSInterface />
    </div>
  )
}
