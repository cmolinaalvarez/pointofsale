import { Concept } from '@/app/types/concept';
import { useState } from 'react';
import { Eye, Pencil } from 'lucide-react';
import { BotonAccion, BotonEstado } from '@/components/ui/buttons';

interface ConceptDetailModalProps { concept: Concept | null; onClose: () => void; }
const ConceptDetailModal: React.FC<ConceptDetailModalProps> = ({ concept, onClose }) => {
  if (!concept) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-lg shadow-xl p-6 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600" aria-label="Cerrar">✕</button>
        <h2 className="text-xl font-semibold mb-4">Detalle de Concepto</h2>
        <div className="space-y-2 text-sm">
          <p><span className="font-medium">ID:</span> {concept.id}</p>
          <p><span className="font-medium">Código:</span> {concept.code}</p> 
          <p><span className="font-medium">Nombre:</span> {concept.name}</p>
          <p><span className="font-medium">Descripción:</span> {concept.description || '—'}</p>
          <p><span className="font-medium">Tipo:</span> {concept.concept_type}</p>
          <p><span className="font-medium">Débito:</span> {concept.debit}</p>
          <p><span className="font-medium">Cuenta Débito:</span> {concept.debit_account_name || concept.debit_account_id}</p>
          <p><span className="font-medium">Crédito:</span> {concept.credit}</p>
          <p><span className="font-medium">Cuenta Crédito:</span> {concept.credit_account_name || concept.credit_account_id}</p>
          <p><span className="font-medium">Estado:</span> {concept.active ? 'Activo' : 'Inactivo'}</p>
          {concept.created_at && <p><span className="font-medium">Creado:</span> {new Date(concept.created_at).toLocaleString()}</p>}
          {concept.updated_at && <p><span className="font-medium">Actualizado:</span> {new Date(concept.updated_at).toLocaleString()}</p>} 
          {concept.user_id && <p><span className="font-medium">Usuario:</span> {concept.user_id}</p>}
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">Cerrar</button>
        </div>
      </div>
    </div>
  );
};

export interface ConceptTableProps {
  concepts: Concept[];
  onEdit?: (concept: Concept) => void;
  onToggleActive?: (id: string, value: boolean) => void;
  loading?: boolean;
  currentPage: number;
  pageSize: number;
}

export const ConceptTable: React.FC<ConceptTableProps> = ({
  concepts = [],
  onEdit,
  onToggleActive,
  loading = false,
  currentPage,
  pageSize,
}) => {
  const [detailConcept, setDetailConcept] = useState<Concept | null>(null);
  const startNumber = (currentPage - 1) * pageSize + 1;

  if (loading) {
    return <div className="animate-pulse">...</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="min-w-full table-auto border border-gray-200">
        <thead>
          <tr className="bg-gradient-to-r from-green-500 to-green-700">
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-12">N°</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-32">Código</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Nombre</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Tipo</th>
            {/* ✅ Nuevas columnas para cuentas */}
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Cuenta Débito</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Cuenta Crédito</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-20">Estado</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-24">Acción</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {concepts.length === 0 ? (
            <tr>
              <td colSpan={8} className="text-center py-8 text-gray-500 text-lg">
                <span role="img" aria-label="Caja vacía">📦</span> No existen conceptos disponibles
              </td>
            </tr>
          ) : (
            concepts.map((concept, idx) => (
              <tr key={concept.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-3 py-2 text-sm text-gray-900 w-12 text-center">
                  {startNumber + idx}
                </td>
                <td className="px-3 py-2 text-sm font-mono text-gray-900 w-32 truncate" title={concept.code}>
                  {concept.code}
                </td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate" title={concept.name}>
                  {concept.name}
                </td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate" title={concept.concept_type}>
                  {concept.concept_type}
                </td>
                {/* ✅ Nuevas celdas para nombres de cuentas */}
                <td className="px-3 py-2 text-sm text-gray-900 w-48 truncate" 
                    title={concept.debit_account_name || concept.debit_account_id}>
                  {concept.debit_account_name || `ID: ${concept.debit_account_id}`}
                </td>
                <td className="px-3 py-2 text-sm text-gray-900 w-48 truncate" 
                    title={concept.credit_account_name || concept.credit_account_id}>
                  {concept.credit_account_name || `ID: ${concept.credit_account_id}`}
                </td>
                <td className="px-2 py-2 text-sm text-center">
                  <BotonEstado
                    active={!!concept.active}
                    onClick={() => onToggleActive && onToggleActive(concept.id, !concept.active)}
                    titleWhenActive="Desactivar concepto"
                    titleWhenInactive="Activar concepto"
                  />
                </td>
                <td className="px-2 py-2 text-sm font-medium flex flex-wrap gap-1 justify-center">
                  <BotonAccion
                    type="button"
                    onClick={() => setDetailConcept(concept)}
                    aria-label="Ver concepto"
                    title="Ver concepto"
                    className="text-indigo-600 hover:text-indigo-700"
                  >
                    <Eye className="h-4 w-4" />
                  </BotonAccion>
                  {onEdit && (
                    <BotonAccion
                      type="button"
                      onClick={() => onEdit(concept)}
                      aria-label="Editar concepto"
                      title="Editar concepto"
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
      <ConceptDetailModal concept={detailConcept} onClose={() => setDetailConcept(null)} />
    </div>
  );
};