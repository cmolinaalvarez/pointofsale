"use client";
import { useDivisions } from "@/hooks/useDivisions";
import { useMunicipalities } from "@/hooks/useMunicipalities";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useState } from "react";
import { MunicipalityTable } from "@/components/MunicipalityTable";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EditMunicipalityModal } from "@/components/EditMunicipalityModal";
import { CreateMunicipalityModal } from "@/components/CreateMunicipalityModal";

export default function MunicipalitiesPage() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingToggle, setPendingToggle] = useState<{ id: string; value: boolean } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const { token } = useAuth();
  const [search, setSearch] = useState('');

  const { divisions, loading: loadingDivisions } = useDivisions(token);
  
  const {
    municipalities,
    total,
    loading,
    error,
    refetch,
    clearError,
    updateMunicipality,
    createMunicipality,
    page,
    pageSize,
    totalPages,
    setPage,
    setPageSize
  } = useMunicipalities(token, search);

  const [editing, setEditing] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    console.log("DIVISIONS:::::",municipalities);
    setIsClient(true);
  }, [token]);

  // Debug: revisar datos de municipios cuando cambien
  useEffect(() => {
    if (municipalities.length > 0) {
      console.log("🏢 Municipio de ejemplo:", municipalities[0]);
      console.log("🏢 Municipio name:", municipalities[0].division_name);
      console.log("🏢 Municipio ID:", municipalities[0].division_id);
    }
  }, [municipalities]);

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
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6">
          <p className="font-semibold text-red-700">{error}</p>
          <button onClick={() => { clearError(); refetch(); }} className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm">Reintentar</button>
        </div>
      )}

      <div className="bg-white shadow rounded p-4 space-y-6">
        {/* Encabezado y acciones */}
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Lista de Municipios ({total})</h3>
          <div className="flex gap-2 items-center">
            <span className="font-bold text-green-600 text-2xl mr-6">Municipios</span>
            <button
              onClick={() => refetch()}
              title="Refrescar"
              aria-label="Refrescar"
              className="p-2 rounded bg-green-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              title="Nueva Categoría"
              aria-label="Nueva Categoría"
              className="p-2 rounded bg-blue-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-green-500"
            >
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
            placeholder="Buscar categoría por nombre..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
        </div>

        {/* Indicador de carga */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <span className="animate-spin h-8 w-8 border-4 border-green-600 border-t-transparent rounded-full mb-4"></span>
            <span className="text-green-700 font-semibold text-lg">Cargando municipios...</span>
          </div>
        ) : (
          <>
            <MunicipalityTable
              municipalities={municipalities}
              loading={loading}
              onEdit={(c) => { setEditing(c); }}
              onToggleActive={(id, val) => {
                setPendingToggle({ id, value: val });
                setConfirmOpen(true);
              }}
              currentPage={page}
              pageSize={pageSize}
            />
            <div className="flex items-center gap-4 flex-wrap text-sm">
              <div className="flex items-center gap-2">
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
              <div className="text-gray-500">
                {total > 0 ? (
                  `Mostrando ${(page-1)*pageSize + 1}-${Math.min(page*pageSize, total)} de ${total}`
                ) : (
                  'No hay municipios para mostrar'
                )}
              </div>
            </div>
          </>
        )}

        <ConfirmDialog
          open={confirmOpen}
          title={pendingToggle?.value ? "Confirmar activación" : "Confirmar inactivación"}
          message={pendingToggle?.value ? "¿Está seguro que desea activar esta categoría?" : "¿Está seguro que desea inactivar esta categoría?"}
          confirmText={pendingToggle?.value ? "Sí, activar" : "Sí, inactivar"}
          cancelText="Cancelar"
          onConfirm={async () => {
            if (pendingToggle) {
              const municipality = municipalities.find(d => d.id === pendingToggle.id);
              if (municipality) {
                const updateData: any = {
                  id: municipality.id,
                  name: municipality.name,                  
                  active: pendingToggle.value,
                  division_code: municipality.division_code,
                  division_id: municipality.division_id  // Corregido: era category_id
                };
                if (municipality.code) updateData.code = municipality.code;
                console.log("🔄 Actualizando división:", updateData);
                try {
                  await updateMunicipality(updateData);
                  await refetch();
                  console.log("✅ División actualizada exitosamente");
                } catch (error) {
                  console.error("❌ Error al actualizar división:", error);
                }
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
      <EditMunicipalityModal
        municipality={editing}
        divisions={divisions || []}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={async (data) => {
          setSaving(true);
          await updateMunicipality(data);
          setSaving(false);
          setEditing(null);
          refetch();
        }}
      />
      <CreateMunicipalityModal
        open={showCreate}
        divisions={divisions || []}
        saving={saving}
        onClose={() => setShowCreate(false)}
        onSave={async (data) => {
          setSaving(true);
          await createMunicipality(data);
          setSaving(false);
          setShowCreate(false);
          refetch();
        }}
      />
    </div>
  );
}