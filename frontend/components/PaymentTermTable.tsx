import { PaymentTerm } from "@/app/types/paymentTerm";
import { BotonAccion, BotonEstado } from "@/components/ui/buttons";
import { Eye, Pencil } from "lucide-react";
import { useState } from "react";

export function PaymentTermTable({
  items, onEdit, onToggleActive, loading, currentPage, pageSize,
}: {
  items: PaymentTerm[];
  onEdit?: (x: PaymentTerm) => void;
  onToggleActive?: (id: string, val: boolean) => void;
  loading?: boolean;
  currentPage: number;
  pageSize: number;
}) {
  const [detail, setDetail] = useState<PaymentTerm | null>(null);
  const start = (currentPage - 1) * pageSize + 1;

  if (loading) return <div className="animate-pulse h-10 bg-gray-200 rounded" />;

  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="min-w-full table-auto border border-gray-200">
        <thead>
          <tr className="bg-gradient-to-r from-green-500 to-green-700">
            <th className="px-3 py-2 text-left text-white font-bold">N°</th>
            <th className="px-3 py-2 text-left text-white font-bold">Código</th>
            <th className="px-3 py-2 text-left text-white font-bold">Nombre</th>
            <th className="px-3 py-2 text-left text-white font-bold">Días</th>
            <th className="px-3 py-2 text-center text-white font-bold">Estado</th>
            <th className="px-3 py-2 text-center text-white font-bold">Acción</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y">
          {items.length === 0 ? (
            <tr><td colSpan={6} className="text-center py-8 text-gray-500">Sin términos</td></tr>
          ) : items.map((it, idx) => (
            <tr key={it.id} className="hover:bg-gray-50">
              <td className="px-3 py-2 text-sm text-center">{start + idx}</td>
              <td className="px-3 py-2 text-sm font-mono">{it.code}</td>
              <td className="px-3 py-2 text-sm">{it.name}</td>
              <td className="px-3 py-2 text-sm text-center">{it.days}</td>
              <td className="px-2 py-2 text-sm text-center">
                <BotonEstado active={!!it.active} onClick={() => onToggleActive?.(it.id, !it.active)} />
              </td>
              <td className="px-2 py-2 text-sm text-center">
                <div className="flex gap-1 justify-center">
                  <BotonAccion onClick={() => setDetail(it)} title="Ver"><Eye className="h-4 w-4" /></BotonAccion>
                  {onEdit && <BotonAccion onClick={() => onEdit(it)} title="Editar"><Pencil className="h-4 w-4" /></BotonAccion>}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {detail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white w-full max-w-md rounded p-6 relative">
            <button onClick={() => setDetail(null)} className="absolute top-3 right-3 text-gray-400">✕</button>
            <h2 className="text-lg font-semibold mb-3">Detalle</h2>
            <pre className="bg-gray-100 p-3 rounded max-h-80 overflow-auto text-xs">{JSON.stringify(detail, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
