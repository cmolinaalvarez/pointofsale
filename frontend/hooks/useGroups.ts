import { useState, useEffect, useCallback } from "react";
import { Group, CreateGroupData, UpdateGroupData, mapGroup, GroupListResponseDTO } from "@/app/types/group";
import { groupService } from "@/app/services/groupService";

// Type guards para verificar la estructura de la respuesta
function isGroupListResponseDTO(response: any): response is GroupListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isGroupArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre marcas
export function useGroups(token: string | null, search: string = "") {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error("Error completo en useGroup:", err);
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
  const fetchGroups = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await groupService.getGroups(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setGroups(response.items.map(mapGroup));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setGroups(response.map(mapGroup));
        setTotal(response.length);
      } else {
        setGroups([]);
        setTotal(0);
        console.warn("Formato de respuesta no reconocido:", response);
      }
    } catch (err) {
      setError(handleError(err));
      setGroups([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  // Efecto para cargar marcas cada vez que cambian los parámetros
  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

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
  const createGroup = async (subCategoryData: CreateGroupData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newGroupDTO = await groupService.createGroup(subCategoryData, token);
      setGroups((prev) => [...prev, mapGroup(newGroupDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una marca existente
  const updateGroup = async (subCategoryData: UpdateGroupData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedGroupDTO = await groupService.updateGroup(subCategoryData.id, subCategoryData, token);
      const updated = mapGroup(updatedGroupDTO);
      setGroups((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una marca
  const deleteGroup = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await groupService.deleteGroup(id, token);
      setGroups((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    groups,
    loading,
    error,
    refetch: fetchGroups,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createGroup,
    updateGroup,
    deleteGroup,
    clearError: () => setError(null),
  };
}