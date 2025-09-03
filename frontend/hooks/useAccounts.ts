import { useState, useEffect, useCallback } from "react";
import { 
  Account, 
  CreateAccountData, 
  UpdateAccountData, 
  mapAccount, 
  AccountListResponseDTO,
  AccountTypeEnum 
} from "@/app/types/account";
import { accountService } from "@/app/services/accountService";

export function useAccounts(token: string | null, search: string = "") {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountTypeEnum, setAccountTypeEnum] = useState<AccountTypeEnum>({}); // ✅ Estado para el enum
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const handleError = (err: unknown): string => {
    console.error("Error completo en useAccount:", err);
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

  const fetchAccounts = useCallback(async () => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const skip = (page - 1) * pageSize;
      const response = await accountService.getAccounts(token, { skip, limit: pageSize, search });
      
      // ✅ VERIFICACIÓN CON ENUM
      if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
        setAccounts(response.items.map(mapAccount));
        setTotal(response.total ?? response.items.length);
        
        // ✅ GUARDAR EL ENUM DINÁMICO
        if ('account_type_enum' in response && response.account_type_enum && typeof response.account_type_enum === 'object') {
          setAccountTypeEnum(response.account_type_enum as AccountTypeEnum);
        } else {
          // ✅ FALLBACK
          setAccountTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
        }
      } else {
        setAccounts([]);
        setTotal(0);
        setAccountTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
      }
    } catch (err) {
      setError(handleError(err));
      setAccounts([]);
      setTotal(0);
      setAccountTypeEnum({ E: "Entrada", S: "Salida", N: "Neutral" });
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, search]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const goToPage = useCallback((newPage: number) => {
    const validatedPage = Math.max(1, Math.min(newPage, totalPages));
    setPage(validatedPage);
  }, [totalPages]);

  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const createAccount = async (accountData: CreateAccountData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const newAccountDTO = await accountService.createAccount(accountData, token);
      setAccounts((prev) => [...prev, mapAccount(newAccountDTO)]);
      setTotal((t) => t + 1);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const updateAccount = async (accountData: UpdateAccountData): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      const updatedAccountDTO = await accountService.updateAccount(accountData.id, accountData, token);
      const updated = mapAccount(updatedAccountDTO);
      setAccounts((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const deleteAccount = async (id: string): Promise<boolean> => {
    if (!token) {
      setError("Token de autenticación no válido");
      return false;
    }
    try {
      setError(null);
      await accountService.deleteAccount(id, token);
      setAccounts((prev) => prev.filter((b) => b.id !== id));
      setTotal((t) => Math.max(0, t - 1));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  return {
    accounts,
    accountTypeEnum, // ✅ Exponer el enum
    loading,
    error,
    refetch: fetchAccounts,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize: changePageSize,
    createAccount,
    updateAccount,
    deleteAccount,
    clearError: () => setError(null),
  };
}