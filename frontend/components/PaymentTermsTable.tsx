import { PaymentTerm } from '@/app/types/paymentTerms';
import { useState } from 'react';
import { Eye, Pencil } from 'lucide-react';
import { BotonAccion, BotonEstado } from '@/components/ui/buttons';

interface PaymentTermDetailModalProps { paymentTerm: PaymentTerm | null; onClose: () => void; }
const PaymentTermDetailModal: React.FC<PaymentTermDetailModalProps> = ({ paymentTerm, onClose }) => {
  if (!paymentTerm) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-lg shadow-xl p-6 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600" aria-label="Cerrar">✕</button>
        <h2 className="text-xl font-semibold mb-4">Detalle de Término de Pago</h2>
        <div className="space-y-2 text-sm">
          <p><span className="font-medium">ID:</span> {paymentTerm.id}</p>
          <p><span className="font-medium">Código:</span> {paymentTerm.code}</p> 
          <p><span className="font-medium">Nombre:</span> {paymentTerm.name}</p>
          <p><span className="font-medium">Descripción:</span> {paymentTerm.description || '—'}</p>
          <p><span className="font-medium">Días netos:</span> {paymentTerm.days || '—'}</p>
          <p><span className="font-medium">% Descuento:</span> {paymentTerm.discountPercent || '—'}</p>
          <p><span className="font-medium">Días descuento:</span> {paymentTerm.discountDays || '—'}</p>
          <p><span className="font-medium">Base:</span> {paymentTerm.basis || '—'}</p>
          <p><span className="font-medium">Estado:</span> {paymentTerm.active ? 'Activo' : 'Inactivo'}</p>
          {paymentTerm.createdAt && <p><span className="font-medium">Creado:</span> {new Date(paymentTerm.createdAt).toLocaleString()}</p>}
          {paymentTerm.updatedAt && <p><span className="font-medium">Actualizado:</span> {new Date(paymentTerm.updatedAt).toLocaleString()}</p>} 
          {paymentTerm.userId && <p><span className="font-medium">Usuario actualización:</span> {paymentTerm.userId}</p>}
        </div>
        <pre className="mt-4 bg-gray-100 rounded p-3 max-h-48 overflow-auto text-xs">{JSON.stringify(paymentTerm, null, 2)}</pre>
        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">Cerrar</button>
        </div>
      </div>
    </div>
  );
};

export interface PaymentTermTableProps {
  paymentTerms: PaymentTerm[];
  onEdit?: (paymentTerm: PaymentTerm) => void;
  onToggleActive?: (id: string, value: boolean) => void;
  loading?: boolean;
  currentPage: number;
  pageSize: number;
}

export const PaymentTermTable: React.FC<PaymentTermTableProps> = ({
  paymentTerms = [],
  onEdit,
  onToggleActive,
  loading = false,
  currentPage,
  pageSize,
}) => {
  const [detailPaymentTerm, setDetailPaymentTerm] = useState<PaymentTerm | null>(null);
  
  const startNumber = (currentPage - 1) * pageSize + 1;

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded mb-4"></div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="min-w-full table-auto border border-gray-200">
        <thead>
          <tr className="bg-gradient-to-r from-blue-500 to-blue-700">
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-12">N°</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-32">Código</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Nombre</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-24">Días</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-32">Base</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-20" title="Estado">Estado</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-24" title="Acción">Acción</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {paymentTerms.length === 0 ? (
            <tr>
              <td colSpan={7} className="text-center py-8 text-gray-500 text-lg">
                <span role="img" aria-label="Caja vacía">📦</span> No existen términos de pago disponibles
              </td>
            </tr>
          ) : (
            paymentTerms.map((paymentTerm, idx) => (
              <tr key={paymentTerm.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-3 py-2 text-sm text-gray-900 w-12 text-center">
                  {startNumber + idx}
                </td>
                <td className="px-3 py-2 text-sm font-mono text-gray-900 w-32 truncate leading-tight" title={paymentTerm.code}>{paymentTerm.code}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={paymentTerm.name}>{paymentTerm.name}</td>
                <td className="px-3 py-2 text-sm text-gray-900 w-24 text-center">{paymentTerm.days || '—'}</td>
                <td className="px-3 py-2 text-sm text-gray-900 w-32 truncate leading-tight" title={paymentTerm.basis}>{paymentTerm.basis || '—'}</td>
                <td className="px-2 py-2 text-sm text-center">
                  <BotonEstado
                    active={!!paymentTerm.active}
                    onClick={() => onToggleActive && onToggleActive(paymentTerm.id, !paymentTerm.active)}
                    titleWhenActive="Desactivar término de pago"
                    titleWhenInactive="Activar término de pago"
                  />
                </td>
                <td className="px-2 py-2 text-sm font-medium flex flex-wrap gap-1 justify-center">
                  <BotonAccion
                    type="button"
                    onClick={() => setDetailPaymentTerm(paymentTerm)}
                    aria-label="Ver término de pago"
                    title="Ver término de pago"
                    className="text-indigo-600 hover:text-indigo-700"
                  >
                    <Eye className="h-4 w-4" />
                  </BotonAccion>
                  {onEdit && (
                    <BotonAccion
                      type="button"
                      onClick={() => onEdit(paymentTerm)}
                      aria-label="Editar término de pago"
                      title="Editar término de pago"
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Pencil className="h-4 w-4" />
                    </BotonAccion>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      <PaymentTermDetailModal paymentTerm={detailPaymentTerm} onClose={() => setDetailPaymentTerm(null)} />
    </div>
  );
};