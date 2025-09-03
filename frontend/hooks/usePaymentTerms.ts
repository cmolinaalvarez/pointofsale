import { useState, useEffect, useCallback } from "react";
import {
  PaymentTerm, CreatePaymentTermData, UpdatePaymentTermData,
  mapPaymentTerm, PaymentTermListResponseDTO
} from "@/app/types/paymentTerm";
import { paymentTermService } from "@/app/services/paymentTermService";

export function usePaymentTerms(token: string | null, search: string = "") {
  const [items, setItems] = useState<PaymentTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const handleError = (err: unknown) => {
    const msg = err instanceof Error ? err.message : "Error inesperado";
    setError(msg);
    if (msg.includes("expirado") || msg.includes("inválido")) window.location.href = "/login";
  };

  const fetchAll = useCallback(async () => {
    if (!token) { setError("Token inválido"); return; }
    setLoading(true); setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const res: PaymentTermListResponseDTO = await paymentTermService.list(token, { skip, limit: pageSize, search });
      setItems(res.items.map(mapPaymentTerm));
      setTotal(res.total ?? res.items.length);
    } catch (e) { handleError(e); }
    finally { setLoading(false); }
  }, [token, page, pageSize, search]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const createItem = async (data: CreatePaymentTermData) => {
    if (!token) return false;
    try {
      const dto = await paymentTermService.create(data, token);
      setItems((prev) => [...prev, mapPaymentTerm(dto)]);
      setTotal((t) => t + 1);
      return true;
    } catch (e) { handleError(e); return false; }
  };

  const updateItem = async (data: UpdatePaymentTermData) => {
    if (!token) return false;
    try {
      const dto = await paymentTermService.update(data.id, data, token);
      const mapped = mapPaymentTerm(dto);
      setItems((prev) => prev.map((x) => (x.id === mapped.id ? mapped : x)));
      return true;
    } catch (e) { handleError(e); return false; }
  };

  return {
    items, loading, error, total, page, pageSize, totalPages,
    setPage: (p: number) => setPage(Math.max(1, Math.min(p, totalPages))),
    setPageSize: (n: number) => { setPageSize(n); setPage(1); },
    refetch: fetchAll, createItem, updateItem, clearError: () => setError(null),
  };
}
