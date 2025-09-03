import { useState, useEffect, useCallback } from "react";
import { Country, CreateCountryData, UpdateCountryData, mapCountry, CountryListResponseDTO } from "@/app/types/country";
import { countryService } from "@/app/services/countryService";

// Type guards para verificar la estructura de la respuesta
function isCountryListResponseDTO(response: any): response is CountryListResponseDTO {
  return response && typeof response === 'object' && 'items' in response && Array.isArray(response.items);
}

function isCountryArray(response: any): response is any[] {
  return Array.isArray(response);
}

// Hook principal para gestionar el listado y acciones sobre paises
export function useCountries(token: string | null, search: string = "") {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Función para traducir errores técnicos a mensajes amigables
  const handleError = (err: unknown): string => {
    console.error("Error completo en useCountry:", err);
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

  // Función para obtener paises desde el backend, considerando paginación
  const fetchCountries = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      // Envía el filtro de búsqueda al backend
      const response = await countryService.getCountries(token, { skip, limit: pageSize, search });
      // ✅ VERIFICACIÓN MEJORADA DE TIPOS
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setCountries(response.items.map(mapCountry));
        setTotal(response.total ?? response.items.length);
      } else if (Array.isArray(response)) {
        setCountries(response.map(mapCountry));
        setTotal(response.length);
      } else {
        setCountries([]);
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

  // Efecto para cargar paises cada vez que cambian los parámetros
  useEffect(() => {
    fetchCountries();
  }, [fetchCountries]);

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

  // Función para crear una nueva país
  const createCountry = async (countryData: CreateCountryData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newCountryDTO = await countryService.createCountry(countryData, token);
      setCountries((prev) => [...prev, mapCountry(newCountryDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para actualizar una país existente
  const updateCountry = async (countryData: UpdateCountryData): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedCountryDTO = await countryService.updateCountry(countryData.id, countryData, token);
      const updated = mapCountry(updatedCountryDTO);
      setCountries((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Función para eliminar una país
  const deleteCountry = async (id: string): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await countryService.deleteCountry(id, token);
      setCountries((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  // Retorna todas las funciones y estados necesarios para el frontend
  return {
    countries,
    loading,
    error,
    refetch: fetchCountries,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createCountry,
    updateCountry,
    deleteCountry,
    clearError: () => setError(null),
  };
}