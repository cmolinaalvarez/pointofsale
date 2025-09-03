import { Municipality } from '@/app/types/municipality';
import { useState } from 'react';
import { Eye, Pencil } from 'lucide-react';
import { BotonAccion, BotonEstado } from '@/components/ui/buttons';

interface MunicipalityDetailModalProps { municipality: Municipality | null; onClose: () => void; }
const MunicipalityDetailModal: React.FC<MunicipalityDetailModalProps> = ({ municipality, onClose }) => {
  if (!municipality) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-lg shadow-xl p-6 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600" aria-label="Cerrar">✕</button>
        <h2 className="text-xl font-semibold mb-4">Detalle de División</h2>
        <div className="space-y-2 text-sm">
          <p><span className="font-medium">ID:</span> {municipality.id}</p>
          <p><span className="font-medium">Código:</span> {municipality.code}</p> 
          <p><span className="font-medium">Nombre:</span> {municipality.name}</p>
          <p><span className="font-medium">Categoría:</span> {municipality.division_name}</p>
          <p><span className="font-medium">Estado:</span> {municipality.active ? 'Activa' : 'Inactiva'}</p>
          {municipality.createdAt && <p><span className="font-medium">Creada:</span> {new Date(municipality.createdAt).toLocaleString()}</p>}
          {municipality.updatedAt && <p><span className="font-medium">Actualizada:</span> {new Date(municipality.updatedAt).toLocaleString()}</p>} 
          {municipality.userId && <p><span className="font-medium">Usuario actualización:</span> {municipality.userId}</p>}
        </div>
        <pre className="mt-4 bg-gray-100 rounded p-3 max-h-48 overflow-auto text-xs">{JSON.stringify(municipality, null, 2)}</pre>
        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">Cerrar</button>
        </div>
      </div>
    </div>
  );
};

// ✅ SOLUCIÓN: SOLO UNA INTERFACE MunicipalityTableProps COMBINADA
export interface MunicipalityTableProps {
  municipalities: Municipality[];
  onEdit?: (municipality: Municipality) => void;
  onToggleActive?: (id: string, value: boolean) => void;
  loading?: boolean;
  currentPage: number;      // ✅ Nuevo prop: página actual
  pageSize: number;         // ✅ Nuevo prop: tamaño de página
}

export const MunicipalityTable: React.FC<MunicipalityTableProps> = ({
  municipalities = [], // <-- valor por defecto
  onEdit,
  onToggleActive,
  loading = false,
  currentPage,              // ✅ Recibe la página actual
  pageSize,                 // ✅ Recibe el tamaño de página
}) => {
  const [detailMunicipality, setDetailMunicipality] = useState<Municipality | null>(null);
  
  // ✅ Calcula el número inicial basado en la página y tamaño
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
          <tr className="bg-gradient-to-r from-green-500 to-green-700">
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-12">N°</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-32">Código</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Nombre</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">División</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-20" title="Estado">Estado</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-24" title="Acción">Acción</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {municipalities.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center py-8 text-gray-500 text-lg">
                <span role="img" aria-label="Caja vacía">📦</span> No existen municipalityes disponibles
              </td>
            </tr>
          ) : (
            municipalities.map((municipality, idx) => (
              <tr key={municipality.id} className="hover:bg-gray-50 transition-colors">
                {/* ✅ Número consecutivo global (no se reinicia por página) */}
                <td className="px-3 py-2 text-sm text-gray-900 w-12 text-center">
                  {startNumber + idx}
                </td>
                <td className="px-3 py-2 text-sm font-mono text-gray-900 w-32 truncate leading-tight" title={municipality.code}>{municipality.code}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={municipality.name}>{municipality.name}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={municipality.division_name}>{municipality.division_name}</td>
                <td className="px-2 py-2 text-sm text-center">
                  <BotonEstado
                    active={!!municipality.active}
                    onClick={() => onToggleActive && onToggleActive(municipality.id, !municipality.active)}
                    titleWhenActive="Desactivar división"
                    titleWhenInactive="Activar división"
                  />
                </td>
                <td className="px-2 py-2 text-sm font-medium flex flex-wrap gap-1 justify-center">
                  <BotonAccion
                    type="button"
                    onClick={() => setDetailMunicipality(municipality)}
                    aria-label="Ver marca"
                    title="Ver marca"
                    className="text-indigo-600 hover:text-indigo-700"
                  >
                    <Eye className="h-4 w-4" />
                  </BotonAccion>
                  {onEdit && (
                    <BotonAccion
                      type="button"
                      onClick={() => onEdit(municipality)}
                      aria-label="Editar marca"
                      title="Editar marca"
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
      <MunicipalityDetailModal municipality={detailMunicipality} onClose={() => setDetailMunicipality(null)} />
    </div>
  );
};