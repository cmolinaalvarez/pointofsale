import { useState, useEffect, useCallback } from 'react';
import { categoryService } from '@/app/services/categoryService';
import { Category, CreateCategoryData, UpdateCategoryData, mapCategory, CategoryListResponseDTO } from '@/app/types/category';

// Type guards para verificar la estructura de la respuesta
function isCategoryListResponseDTO(response: any): response is CategoryListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isCategoryArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre categorías
export function useCategories(token: string | null, search: string = "") {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error('Error completo en useCategories:', err);
    if (err instanceof Error) {
      if (err.message.includes('401')) return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
      if (err.message.includes('403')) return 'No tienes permisos para acceder a esta información.';
      if (err.message.includes('404')) return 'El recurso solicitado no fue encontrado.';
      if (err.message.includes('500')) return 'Error interno del servidor. Intenta nuevamente más tarde.';
      if (err.message.includes('timeout') || err.message.includes('Network'))
        return 'Tiempo de espera agotado. Verifica tu conexión.';
      return err.message;
    }
    return 'Error inesperado al procesar la solicitud';
  };

  // Función para obtener categorías desde el backend, considerando paginación
  const fetchCategories = useCallback(async () => {
    if (!token || token.trim() === '') {
      setError('Token de autenticación no válido');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await categoryService.getCategories(token, { skip, limit: pageSize, search });
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setCategories(response.items.map(mapCategory));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setCategories(response.map(mapCategory));
        setTotal(response.length);
      } else {
        setCategories([]);
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
      setCategories([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  // Efecto para cargar categorías cada vez que cambian los parámetros
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

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

  // Función para crear una nueva categoría
  const createCategory = async (categoryData: CreateCategoryData): Promise<boolean> => {
    if (!token || token.trim() === '') {
      setError('Token de autenticación no válido');
      return false;
    }
    try {
      setError(null);
      const newCategoryDTO = await categoryService.createCategory(categoryData, token);
      setCategories((prev) => [...prev, mapCategory(newCategoryDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una categoría existente
  const updateCategory = async (categoryData: UpdateCategoryData): Promise<boolean> => {
    if (!token || token.trim() === '') {
      setError('Token de autenticación no válido');
      return false;
    }
    try {
      setError(null);
      const updatedCategoryDTO = await categoryService.updateCategory(categoryData.id, categoryData, token);
      const updated = mapCategory(updatedCategoryDTO);
      setCategories((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una categoría
  const deleteCategory = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === '') {
      setError('Token de autenticación no válido');
      return false;
    }
    try {
      setError(null);
      await categoryService.deleteCategory(id, token);
      setCategories((prev) => prev.filter((c) => c.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    categories,
    loading,
    error,
    refetch: fetchCategories,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createCategory,
    updateCategory,
    deleteCategory,
    clearError: () => setError(null),
  };
}