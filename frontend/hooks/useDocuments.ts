import { useState, useEffect, useCallback } from "react";
import { 
  Document, 
  CreateDocumentData, 
  UpdateDocumentData, 
  mapDocument, 
  DocumentListResponseDTO,
  DocumentTypeEnum 
} from "@/app/types/document";
import { documentService } from "@/app/services/documentService";

export function useDocuments(token: string | null, search: string = "") {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentTypeEnum, setDocumentTypeEnum] = useState<DocumentTypeEnum>({}); // ✅ Estado para el enum
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const handleError = (err: unknown): string => {
    console.error("Error completo en useDocument:", err);
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

  const fetchDocuments = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      const response = await documentService.getDocuments(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN CON ENUM
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setDocuments(response.items.map(mapDocument));
        setTotal(response.total ?? response.items.length);
        
        // ✅ GUARDAR EL ENUM DINÁMICO
        if ('document_type_enum' in response && response.document_type_enum && typeof response.document_type_enum === 'object') {
          setDocumentTypeEnum(response.document_type_enum as DocumentTypeEnum);
        } else {
          // ✅ FALLBACK
          setDocumentTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
        }
      } else {
        setDocuments([]);
        setTotal(0);
        setDocumentTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
      }
    } catch (err) {
      setError(handleError(err));
      setDocuments([]);
      setTotal(0);
      setDocumentTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const goToPage = useCallback((newPage: number) => {
    const validatedPage = Math.max(1, Math.min(newPage, totalPages));
    setPage(validatedPage);
  }, [totalPages]);

  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const createDocument = async (documentData: CreateDocumentData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newDocumentDTO = await documentService.createDocument(documentData, token);
      setDocuments((prev) => [...prev, mapDocument(newDocumentDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const updateDocument = async (documentData: UpdateDocumentData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedDocumentDTO = await documentService.updateDocument(documentData.id, documentData, token);
      const updated = mapDocument(updatedDocumentDTO);
      setDocuments((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const deleteDocument = async (id: string): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await documentService.deleteDocument(id, token);
      setDocuments((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  return {
    documents,
    documentTypeEnum, // ✅ Exponer el enum
    loading,
    error,
    refetch: fetchDocuments,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createDocument,
    updateDocument,
    deleteDocument,
    clearError: () => setError(null),
  };
}