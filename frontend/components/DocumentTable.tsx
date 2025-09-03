import { Document } from '@/app/types/document';
import { useState } from 'react';
import { Eye, Pencil } from 'lucide-react';
import { BotonAccion, BotonEstado } from '@/components/ui/buttons';

interface DocumentDetailModalProps { document: Document | null; onClose: () => void; }
const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({ document, onClose }) => {
  if (!document) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-lg shadow-xl p-6 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600" aria-label="Cerrar">✕</button>
        <h2 className="text-xl font-semibold mb-4">Detalle de documento</h2>
        <div className="space-y-2 text-sm">
          <p><span className="font-medium">ID:</span> {document.id}</p>
          <p><span className="font-medium">Código:</span> {document.code}</p> 
          <p><span className="font-medium">Nombre:</span> {document.name}</p>
          <p><span className="font-medium">Descripción:</span> {document.description || '—'}</p>
          <p><span className="font-medium">Estado:</span> {document.active ? 'Activa' : 'Inactiva'}</p>
          {document.createdAt && <p><span className="font-medium">Creada:</span> {new Date(document.createdAt).toLocaleString()}</p>}
          {document.updatedAt && <p><span className="font-medium">Actualizada:</span> {new Date(document.updatedAt).toLocaleString()}</p>} 
          {document.userId && <p><span className="font-medium">Usuario actualización:</span> {document.userId}</p>}
        </div>
        <pre className="mt-4 bg-gray-100 rounded p-3 max-h-48 overflow-auto text-xs">{JSON.stringify(document, null, 2)}</pre>
        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">Cerrar</button>
        </div>
      </div>
    </div>
  );
};

// ✅ SOLUCIÓN: SOLO UNA INTERFACE DocumentTableProps COMBINADA
export interface DocumentTableProps {
  documents: Document[];
  onEdit?: (document: Document) => void;
  onToggleActive?: (id: string, value: boolean) => void;
  loading?: boolean;
  currentPage: number;      // ✅ Nuevo prop: página actual
  pageSize: number;         // ✅ Nuevo prop: tamaño de página
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents = [], // <-- valor por defecto
  onEdit,
  onToggleActive,
  loading = false,
  currentPage,              // ✅ Recibe la página actual
  pageSize,                 // ✅ Recibe el tamaño de página
}) => {
  const [detailDocument, setDetailDocument] = useState<Document | null>(null);
  
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
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Prefijo</th>
            <th className="px-3 py-2 text-left text-white font-bold uppercase tracking-wider w-48">Tipo</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-20" title="Estado">Estado</th>
            <th className="px-2 py-2 text-center text-white font-bold uppercase tracking-wider w-24" title="Acción">Acción</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {documents.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center py-8 text-gray-500 text-lg">
                <span role="img" aria-label="Caja vacía">📦</span> No existen documentos disponibles
              </td>
            </tr>
          ) : (
            documents.map((document, idx) => (
              <tr key={document.id} className="hover:bg-gray-50 transition-colors">
                {/* ✅ Número consecutivo global (no se reinicia por página) */}
                <td className="px-3 py-2 text-sm text-gray-900 w-12 text-center">
                  {startNumber + idx}
                </td>
                <td className="px-3 py-2 text-sm font-mono text-gray-900 w-32 truncate leading-tight" title={document.code}>{document.code}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={document.name}>{document.name}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={document.prefix}>{document.prefix}</td>
                <td className="px-3 py-2 text-sm font-medium text-gray-900 w-48 truncate leading-tight" title={document.document_type}>{document.document_type}</td>
                <td className="px-2 py-2 text-sm text-center">
                  <BotonEstado
                    active={!!document.active}
                    onClick={() => onToggleActive && onToggleActive(document.id, !document.active)}
                    titleWhenActive="Desactivar documento"
                    titleWhenInactive="Activar documento"
                  />
                </td>
                <td className="px-2 py-2 text-sm font-medium flex flex-wrap gap-1 justify-center">
                  <BotonAccion
                    type="button"
                    onClick={() => setDetailDocument(document)}
                    aria-label="Ver documento"
                    title="Ver documento"
                    className="text-indigo-600 hover:text-indigo-700"
                  >
                    <Eye className="h-4 w-4" />
                  </BotonAccion>
                  {onEdit && (
                    <BotonAccion
                      type="button"
                      onClick={() => onEdit(document)}
                      aria-label="Editar documento"
                      title="Editar documento"
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
      <DocumentDetailModal document={detailDocument} onClose={() => setDetailDocument(null)} />
    </div>
  );
};