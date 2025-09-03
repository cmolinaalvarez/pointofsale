"use client";
import { useDocuments } from "@/hooks/useDocuments";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useState } from "react";
import { DocumentTable } from "@/components/DocumentTable";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EditDocumentModal } from "@/components/EditDocumentModal";
import { CreateDocumentModal } from "@/components/CreateDocumentModal";

export default function DocumentsPage() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingToggle, setPendingToggle] = useState<{ id: string; value: boolean } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const { token } = useAuth();
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);

  // ✅ Obtener el enum del hook
  const {
    documents,
    documentTypeEnum, // ✅ Ahora disponible
    total,
    loading,
    error,
    refetch,
    clearError,
    updateDocument,
    createDocument,
    page,
    pageSize,
    totalPages,
    setPage,
    setPageSize
  } = useDocuments(token, search);

  useEffect(() => {
    setIsClient(true);
  }, [token]);

  useEffect(() => {
    setPage(1);
  }, [search, setPage]);

  if (!isClient) return null;
  if (!token) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-red-600">No Token</h1>
        <p>No se encontró token de autenticación</p>
        <button onClick={() => window.location.href = '/login'} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">Ir a Login</button>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Muestra errores si existen */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6">
          <p className="font-semibold text-red-700">{error}</p>
          <button onClick={() => { clearError(); refetch(); }} className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm">Reintentar</button>
        </div>
      )}

      <div className="bg-white shadow rounded p-4 space-y-6">
        {/* Encabezado y acciones */}
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Lista de Documentos ({total})</h3>
          <div className="flex gap-2 items-center">
            <span className="font-bold text-green-700 text-2xl mr-6">Documentos</span>
            {/* Botón para refrescar listado */}
            <button
              onClick={() => refetch()}
              title="Refrescar"
              aria-label="Refrescar"
              className="p-2 rounded bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
            >
              {/* Icono refresh */}
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
            </button>
            {/* Botón para abrir modal de nueva documento */}
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              title="Nueva Categoría"
              aria-label="Nueva Categoría"
              className="p-2 rounded bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-green-500"
            >
              {/* Icono plus */}
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          </div>
        </div>
        {/* Caja de búsqueda */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Buscar documento por nombre..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
        </div>
        {/* Indicador de carga */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <span className="animate-spin h-8 w-8 border-4 border-green-600 border-t-transparent rounded-full mb-4"></span>
            <span className="text-green-700 font-semibold text-lg">Cargando documentos...</span>
          </div>
        ) : (
          <>
            {/* Tabla de documentos paginadas y filtradas por el backend */}
            <DocumentTable
              documents={documents}
              loading={loading}
              onEdit={(c) => { setEditing(c); }}
              onToggleActive={(id, val) => {
                setPendingToggle({ id, value: val });
                setConfirmOpen(true);
              }}
              currentPage={page}       // ✅ Pasa la página actual
              pageSize={pageSize}      // ✅ Pasa el tamaño de página
            />
            {/* Paginación y selección de tamaño de página */}
            <div className="flex items-center gap-4 flex-wrap text-sm">
              <div className="flex items-center gap-2">
                {/* Botones de navegación de página */}
                <button
                  className="px-2 py-1 border border-green-600 rounded disabled:opacity-40"
                  onClick={() => setPage(1)}
                  disabled={page === 1 || loading || totalPages === 0}
                >&laquo;</button>
                <button
                  className="px-2 py-1 border border-green-600 rounded disabled:opacity-40"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1 || loading || totalPages === 0}
                >&lsaquo;</button>
                
                <span className="px-1">Página {page} de {totalPages}</span>
                
                <button
                  className="px-2 py-1 border border-green-600 rounded disabled:opacity-40"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages || loading || totalPages === 0}
                >&rsaquo;</button>
                <button
                  className="px-2 py-1 border border-green-600 rounded disabled:opacity-40"
                  onClick={() => setPage(totalPages)}
                  disabled={page === totalPages || loading || totalPages === 0}
                >&raquo;</button>
              </div>
              
              {/* Selector de tamaño de página */}
              <div className="flex items-center gap-2">
                <label htmlFor="pageSize" className="text-gray-600">Filas:</label>
                <select
                  id="pageSize"
                  className="border border-green-600 rounded px-2 py-1"
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  disabled={loading}
                >
                  {[5,10,20,50].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              
              {/* Información de rango mostrado */}
              <div className="text-gray-500">
                {total > 0 ? (
                  `Mostrando ${(page-1)*pageSize + 1}-${Math.min(page*pageSize, total)} de ${total}`
                ) : (
                  'No hay documentos para mostrar'
                )}
              </div>
            </div>
          </>
        )}
        {/* Modal de confirmación para activar/inactivar documento */}
        <ConfirmDialog
          open={confirmOpen}
          title={pendingToggle?.value ? "Confirmar activación" : "Confirmar inactivación"}
          message={pendingToggle?.value ? "¿Está seguro que desea activar esta documento?" : "¿Está seguro que desea inactivar esta documento?"}
          confirmText={pendingToggle?.value ? "Sí, activar" : "Sí, inactivar"}
          cancelText="Cancelar"
          onConfirm={async () => {
            if (pendingToggle) {
              // Actualiza el estado activo/inactivo de la documento
              const document = documents.find(c => c.id === pendingToggle.id);
              if (document) {
                const updateData: any = {
                  id: document.id,
                  code: document.code,
                  name: document.name,
                  description: document.description ?? undefined,
                  prefix: document.prefix,
                  document_type:document.document_type,
                  active: pendingToggle.value
                };

              if (document.code) updateData.code = document.code;
                await updateDocument(updateData);
                await refetch();
              }
            }
            setConfirmOpen(false);
            setPendingToggle(null);
          }}
          onCancel={() => {
            setConfirmOpen(false);
            setPendingToggle(null);
          }}
        />
      </div>     
      
      <EditDocumentModal
        document={editing}
        documentTypeEnum={documentTypeEnum} // ✅ Pasar el enum
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={async (data) => {
          setSaving(true);
          await updateDocument(data);
          setSaving(false);
          setEditing(null);
          refetch();
        }}
      />
      
      <CreateDocumentModal
        open={showCreate}
        documentTypeEnum={documentTypeEnum} // ✅ Pasar el enum
        saving={saving}
        onClose={() => setShowCreate(false)}
        onSave={async (data) => {
          setSaving(true);
          await createDocument(data);
          setSaving(false);
          setShowCreate(false);
          refetch();
        }}
      />
    </div>
  );
}