import { useState, useEffect, useCallback } from "react";
import { Unit, CreateUnitData, UpdateUnitData, mapUnit, UnitListResponseDTO } from "@/app/types/unit";
import { unitService } from "@/app/services/unitService";

// Type guards para verificar la estructura de la respuesta
function isUnitListResponseDTO(response: any): response is UnitListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isUnitArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre unidades
export function useUnits(token: string | null, search: string = "") {
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error("Error completo en useUnit:", err);
    if (err instanceof Error) {
      if (err.message.includes("401")) return "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.";
      if (err.message.includes("403")) return "No tienes permisos para acceder a esta información.";
      if (err.message.includes("404")) return "El recurso solicitado no fue encontrado.";
      if (err.message.includes("500")) return "Error interno del servidor. Intenta nuevamente más tarde.";
      if (err.message.includes("timeout") || err.message.includes("Network")) 
        return "Tiempo de espera agotado. Verifica tu conexión.";
      return err.message;
    }
    return "Error inesperado al procesar la solicitud";
  };

  // Función para obtener unidades desde el backend, considerando paginación
  const fetchUnits = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await unitService.getUnits(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setUnits(response.items.map(mapUnit));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setUnits(response.map(mapUnit));
        setTotal(response.length);
      } else {
        setUnits([]);
        setTotal(0);
        console.warn("Formato de respuesta no reconocido:", response);
      }
    } catch (err) {
      setError(handleError(err));
      setUnits([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  // Efecto para cargar unidades cada vez que cambian los parámetros
  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  // Calcula el total de páginas para la paginación
  const totalPages = Math.ceil(total / pageSize) || 1;

  // Función para cambiar de página, asegurando que esté dentro de los límites
  const goToPage = useCallback((newPage: number) => {
    const validatedPage = Math.max(1, Math.min(newPage, totalPages));
    setPage(validatedPage);
  }, [totalPages]);

  // Función para cambiar el tamaño de página
  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reiniciar a la primera página
  }, []);

  // Función para crear una nueva unidad
  const createUnit = async (unitData: CreateUnitData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newUnitDTO = await unitService.createUnit(unitData, token);
      setUnits((prev) => [...prev, mapUnit(newUnitDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una unidad existente
  const updateUnit = async (unitData: UpdateUnitData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedUnitDTO = await unitService.updateUnit(unitData.id, unitData, token);
      const updated = mapUnit(updatedUnitDTO);
      setUnits((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una unidad
  const deleteUnit = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await unitService.deleteUnit(id, token);
      setUnits((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    units,
    loading,
    error,
    refetch: fetchUnits,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createUnit,
    updateUnit,
    deleteUnit,
    clearError: () => setError(null),
  };
}