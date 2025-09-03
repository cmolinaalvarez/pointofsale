"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { usePaymentTerms } from "@/hooks/usePaymentTerms";
import { PaymentTermTable } from "@/components/PaymentTermTable";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EditPaymentTermModal } from "@/components/EditPaymentTermModal";
import { CreatePaymentTermModal } from "@/components/CreatePaymentTermModal";
import { SpanishDate } from "@/components/SpanishDate";

export default function PaymentTermsPage() {
  const { token } = useAuth();
  const [isClient, setIsClient] = useState(false);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingToggle, setPendingToggle] = useState<{ id: string; value: boolean } | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const {
    items, total, loading, error, refetch,
    page, pageSize, totalPages, setPage, setPageSize,
    createItem, updateItem, clearError
  } = usePaymentTerms(token, search);

  useEffect(()=>{ setIsClient(true); }, [token]);
  useEffect(()=>{ setPage(1); }, [search, setPage]);
  if (!isClient) return null;

  if (!token) {
    return <div className="p-6">
      <h1 className="text-2xl font-bold text-red-600">No Token</h1>
      <button onClick={()=>window.location.href='/login'} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">Ir a Login</button>
    </div>;
  }

  return (
    <div className="p-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6">
          <p className="font-semibold text-red-700">{error}</p>
          <button onClick={()=>{ clearError(); refetch(); }} className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm">Reintentar</button>
        </div>
      )}

      <div className="bg-white shadow rounded p-4 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Términos de Pago ({total})</h3>
          <div className="flex gap-2 items-center">
            <span className="font-bold text-green-700 text-2xl mr-6">PaymentTerms</span>
            <button onClick={()=>refetch()} className="p-2 rounded bg-blue-600 text-white">↻</button>
            <button onClick={()=>setShowCreate(true)} className="p-2 rounded bg-green-600 text-white">＋</button>
          </div>
        </div>

        <div className="mb-4">
          <input type="text" placeholder="Buscar por código o nombre..."
            value={search} onChange={e=>setSearch(e.target.value)} className="border px-3 py-2 rounded w-full" />
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <span className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mb-4" />
            <span className="text-blue-700 font-semibold text-lg">Cargando…</span>
          </div>
        ) : (
          <>
            <PaymentTermTable
              items={items}
              loading={loading}
              currentPage={page}
              pageSize={pageSize}
              onEdit={(x)=>setEditing(x)}
              onToggleActive={(id, val)=>{ setPendingToggle({ id, value: val }); setConfirmOpen(true); }}
            />

            <div className="flex items-center gap-4 flex-wrap text-sm">
              <div className="flex items-center gap-2">
                <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={()=>setPage(1)} disabled={page===1}>«</button>
                <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={()=>setPage(page-1)} disabled={page===1}>‹</button>
                <span>Página {page} de {totalPages}</span>
                <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={()=>setPage(page+1)} disabled={page===totalPages}>›</button>
                <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={()=>setPage(totalPages)} disabled={page===totalPages}>»</button>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="ps">Filas:</label>
                <select id="ps" className="border rounded px-2 py-1" value={pageSize} onChange={(e)=>setPageSize(Number(e.target.value))}>
                  {[5,10,20,50].map(n=><option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div className="text-gray-500">
                {total>0 ? `Mostrando ${(page-1)*pageSize+1}-${Math.min(page*pageSize,total)} de ${total}` : 'Sin datos'}
              </div>
              <SpanishDate />
            </div>
          </>
        )}

        <ConfirmDialog
          open={confirmOpen}
          title={pendingToggle?.value ? "Confirmar activación" : "Confirmar inactivación"}
          message={pendingToggle?.value ? "¿Activar término?" : "¿Inactivar término?"}
          confirmText={pendingToggle?.value ? "Sí, activar" : "Sí, inactivar"}
          cancelText="Cancelar"
          onConfirm={async ()=>{
            if (pendingToggle) {
              const it = items.find(x=>x.id===pendingToggle.id);
              if (it) {
                await updateItem({ id: it.id, code: it.code, name: it.name, description: it.description ?? undefined, days: it.days, active: pendingToggle.value });
                await refetch();
              }
            }
            setConfirmOpen(false); setPendingToggle(null);
          }}
          onCancel={()=>{ setConfirmOpen(false); setPendingToggle(null); }}
        />
      </div>

      <EditPaymentTermModal
        item={editing}
        saving={saving}
        onClose={()=>setEditing(null)}
        onSave={async (data)=>{
          setSaving(true); await updateItem(data); setSaving(false); setEditing(null); refetch();
        }}
      />

      <CreatePaymentTermModal
        open={showCreate}
        saving={saving}
        onClose={()=>setShowCreate(false)}
        onSave={async (data)=>{
          setSaving(true); await createItem(data); setSaving(false); setShowCreate(false); refetch();
        }}
      />
    </div>
  );
}
