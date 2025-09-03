import { useState, useEffect, useCallback } from "react";
import { Brand, CreateBrandData, UpdateBrandData, mapBrand, BrandListResponseDTO } from "@/app/types/brand";
import { brandService } from "@/app/services/brandService";

// Type guards para verificar la estructura de la respuesta
function isBrandListResponseDTO(response: any): response is BrandListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isBrandArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre marcas
export function useBrands(token: string | null, search: string = "") {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error("Error completo en useBrand:", err);
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
  const fetchBrands = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await brandService.getBrands(token, { skip, limit: pageSize, search });
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setBrands(response.items.map(mapBrand));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setBrands(response.map(mapBrand));
        setTotal(response.length);
      } else {
        setBrands([]);
        setTotal(0);
        console.warn("Formato de respuesta no reconocido:", response);
      }
    } catch (err) {
      const errorMsg = handleError(err);
      setError(errorMsg);
      // --- Manejo automático de token inválido/expirado ---
      // Si el error indica token inválido, redirige al login
      if (errorMsg.includes('Token de autenticación inválido') || errorMsg.includes('Token inválido') || errorMsg.includes('expirado')) {
        // Redirección automática para mejor UX
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  // Efecto para cargar marcas cada vez que cambian los parámetros
  useEffect(() => {
    fetchBrands();
  }, [fetchBrands]);

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
  const createBrand = async (brandData: CreateBrandData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newBrandDTO = await brandService.createBrand(brandData, token);
      setBrands((prev) => [...prev, mapBrand(newBrandDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una marca existente
  const updateBrand = async (brandData: UpdateBrandData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedBrandDTO = await brandService.updateBrand(brandData.id, brandData, token);
      const updated = mapBrand(updatedBrandDTO);
      setBrands((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una marca
  const deleteBrand = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await brandService.deleteBrand(id, token);
      setBrands((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    brands,
    loading,
    error,
    refetch: fetchBrands,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createBrand,
    updateBrand,
    deleteBrand,
    clearError: () => setError(null),
  };
}