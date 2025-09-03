import { useState, useEffect, useCallback } from "react";
import { 
  Concept, 
  CreateConceptData, 
  UpdateConceptData, 
  mapConcept, 
  ConceptListResponseDTO,
  ConceptTypeEnum 
} from "@/app/types/concept";
import { conceptService } from "@/app/services/conceptService";

export function useConcepts(token: string | null, search: string = "") {
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [conceptTypeEnum, setConceptTypeEnum] = useState<ConceptTypeEnum>({}); // ✅ Estado para el enum
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const handleError = (err: unknown): string => {
    console.error("Error completo en useConcept:", err);
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

  const fetchConcepts = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      const response = await conceptService.getConcepts(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN CON ENUM
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setConcepts(response.items.map(mapConcept));
        setTotal(response.total ?? response.items.length);
        
        // ✅ GUARDAR EL ENUM DINÁMICO
        if ('concept_type_enum' in response && response.concept_type_enum && typeof response.concept_type_enum === 'object') {
          setConceptTypeEnum(response.concept_type_enum as ConceptTypeEnum);
        } else {
          // ✅ FALLBACK
          setConceptTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
        }
      } else {
        setConcepts([]);
        setTotal(0);
        setConceptTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
      }
    } catch (err) {
      setError(handleError(err));
      setConcepts([]);
      setTotal(0);
      setConceptTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  useEffect(() => {
    fetchConcepts();
  }, [fetchConcepts]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const goToPage = useCallback((newPage: number) => {
    const validatedPage = Math.max(1, Math.min(newPage, totalPages));
    setPage(validatedPage);
  }, [totalPages]);

  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const createConcept = async (conceptData: CreateConceptData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newConceptDTO = await conceptService.createConcept(conceptData, token);
      setConcepts((prev) => [...prev, mapConcept(newConceptDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const updateConcept = async (conceptData: UpdateConceptData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedConceptDTO = await conceptService.updateConcept(conceptData.id, conceptData, token);
      const updated = mapConcept(updatedConceptDTO);
      setConcepts((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const deleteConcept = async (id: string): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await conceptService.deleteConcept(id, token);
      setConcepts((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  return {
    concepts,
    conceptTypeEnum, // ✅ Exponer el enum
    loading,
    error,
    refetch: fetchConcepts,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createConcept,
    updateConcept,
    deleteConcept,
    clearError: () => setError(null),
  };
}