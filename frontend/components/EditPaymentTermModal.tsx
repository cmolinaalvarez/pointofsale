import { useEffect, useState } from "react";
import { PaymentTerm } from "@/app/types/paymentTerm";
import { ToggleLeft, ToggleRight } from "lucide-react";

export function EditPaymentTermModal({
  item, onClose, onSave, saving=false
}: {
  item: PaymentTerm | null;
  onClose: () => void;
  onSave: (data: { id: string; code: string; name: string; description?: string; days: number; active: boolean }) => Promise<void> | void;
  saving?: boolean;
}) {
  const [code, setCode] = useState(""); const [name, setName] = useState("");
  const [description, setDescription] = useState(""); const [days, setDays] = useState(0);
  const [active, setActive] = useState(true); const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (item) { setCode(item.code || ""); setName(item.name || ""); setDescription(item.description || "");
      setDays(Number(item.days || 0)); setActive(!!item.active); setErr(null); }
  }, [item]);

  if (!item) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return setErr("El código es obligatorio");
    if (!name.trim()) return setErr("El nombre es obligatorio");
    if (days < 0 || days > 3650) return setErr("days debe estar entre 0 y 3650");
    await onSave({ id: item.id, code: code.trim().toUpperCase(), name: name.trim(), description: description.trim() || undefined, days, active });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white w-full max-w-lg rounded-lg shadow border">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Editar Término de Pago</h2>
          <button onClick={onClose} className="text-gray-400">✕</button>
        </div>
        <form onSubmit={submit} className="p-5 space-y-4">
          {err && <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-2 rounded">{err}</div>}
          <div><label className="text-xs">Código</label>
            <input className="w-full border rounded px-3 py-2 text-sm" value={code} onChange={e=>setCode(e.target.value)} disabled={saving} maxLength={32} />
          </div>
          <div><label className="text-xs">Nombre</label>
            <input className="w-full border rounded px-3 py-2 text-sm" value={name} onChange={e=>setName(e.target.value)} disabled={saving} />
          </div>
          <div><label className="text-xs">Descripción</label>
            <textarea className="w-full border rounded px-3 py-2 text-sm min-h-[80px]" value={description} onChange={e=>setDescription(e.target.value)} disabled={saving} />
          </div>
          <div><label className="text-xs">Días</label>
            <input type="number" className="w-full border rounded px-3 py-2 text-sm" value={days} onChange={e=>setDays(parseInt(e.target.value || "0",10))} min={0} max={3650} disabled={saving} />
          </div>
          <div>
            <button type="button" onClick={()=>setActive(a=>!a)} disabled={saving} className="flex items-center gap-2">
              {active ? <ToggleRight className="h-6 w-6 text-green-600" /> : <ToggleLeft className="h-6 w-6 text-gray-400" />}
              <span className={`px-3 py-1 rounded-full text-xs border ${active?'bg-green-50 text-green-700 border-green-200':'bg-gray-100 text-gray-600 border-gray-300'}`}>{active?'Activa':'Inactiva'}</span>
            </button>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded border">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 text-sm rounded bg-blue-600 text-white">{saving?'Guardando...':'Guardar'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
