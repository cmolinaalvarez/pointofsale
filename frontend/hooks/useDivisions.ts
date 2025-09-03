import { useState, useEffect, useCallback } from "react";
import { Division, 
  CreateDivisionData, 
  UpdateDivisionData, 
  mapDivision, 
  DivisionListResponseDTO } from "@/app/types/division";
import { divisionService } from "@/app/services/divisionService";

// Type guards para verificar la estructura de la respuesta
function isDivisionListResponseDTO(response: any): response is DivisionListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isDivisionArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre divisiones
export function useDivisions(token: string | null, search: string = "") {
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error("Error completo en useDivision:", err);
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

  // Función para obtener marcas desde el backend, considerando paginación
  const fetchDivisions = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await divisionService.getDivisions(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setDivisions(response.items.map(mapDivision));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setDivisions(response.map(mapDivision));
        setTotal(response.length);
      } else {
        setDivisions([]);
        setTotal(0);
        console.warn("Formato de respuesta no reconocido:", response);
      }
    } catch (err) {
      setError(handleError(err));
      setDivisions([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  // Efecto para cargar marcas cada vez que cambian los parámetros
  useEffect(() => {
    fetchDivisions();
  }, [fetchDivisions]);

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

  // Función para crear una nueva marca
  const createDivision = async (divisionData: CreateDivisionData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newDivisionDTO = await divisionService.createDivision(divisionData, token);
      setDivisions((prev) => [...prev, mapDivision(newDivisionDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una marca existente
  const updateDivision = async (divisionData: UpdateDivisionData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      console.log("🔄 Enviando datos para actualizar:", divisionData);
      const updatedDivisionDTO = await divisionService.updateDivision(divisionData.id, divisionData, token);
      console.log("✅ Respuesta del servidor:", updatedDivisionDTO);
      const updated = mapDivision(updatedDivisionDTO);
      setDivisions((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      console.error("❌ Error en updateDivision:", err);
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una marca
  const deleteDivision = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await divisionService.deleteDivision(id, token);
      setDivisions((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    divisions,
    loading,
    error,
    refetch: fetchDivisions,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createDivision,
    updateDivision,
    deleteDivision,
    clearError: () => setError(null),
  };
}