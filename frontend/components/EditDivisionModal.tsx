import React, { useEffect, useState } from 'react';
import { Division } from '@/app/types/division';
import { ToggleLeft, ToggleRight } from 'lucide-react';

interface Category {
  id: string;
  name: string;
}

interface EditDivisionModalProps {
  division: Division | null;
  countries: Category[]; // <-- Recibe las categorías
  onClose: () => void;
  onSave: (data: { id: string; code: string; name: string; country_code?: string; iso_3166_2?: string; country_id?: string; active: boolean; category_id: string }) => Promise<void> | void;
  saving?: boolean;
}

export const EditDivisionModal: React.FC<EditDivisionModalProps> = ({
  division,
  countries = [], // <-- valor por defecto
  onClose,
  onSave,
  saving = false
}) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [country_code, setCountryCode] = useState('');
  const [iso_3166_2, setIso31662] = useState('');
  const [country_id, setCountryId] = useState('');
  const [description, setDescription] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [active, setActive] = useState<boolean>(true);

  useEffect(() => {
    if (division) {
      setCode(division.code || '');
      setName(division.name || '');
      setCountryCode(division.country_code|| '');  
      setIso31662(division.iso_3166_2|| ''); 
      setCountryId(division.country_id || ''); // <-- Usar category_id
      setDescription(division.description || '');
      setActive(!!division.active);
      setLocalError(null);
    }
  }, [division]);

  if (!division) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setLocalError('El código es obligatorio');
      return;
    }
    if (!name.trim()) {
      setLocalError('El nombre es obligatorio');
      return;
    }
    if (!country_id) {
      setLocalError('Debe seleccionar una categoría');
      return;
    }
    const payload = {
      id: division.id,
      code: code.trim(),
      name: name.trim(),      
      country_code: country_code.trim(),
      iso_3166_2: iso_3166_2.trim(),
      description: description.trim() || undefined,
      active: Boolean(active),
      country_id // <-- Enviar el UUID
    };
    await onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white w-full max-w-lg rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Editar División</h2>
          <button onClick={onClose} aria-label="Cerrar" className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {localError && <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-2 rounded">{localError}</div>}
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Código</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              disabled={saving}
              maxLength={50}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Nombre</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={saving}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Código país</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={country_code}
              onChange={(e) => setCountryCode(e.target.value)}
              required
              disabled={saving}
             />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">ISO 3166_2</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={iso_3166_2}
              onChange={(e) => setIso31662(e.target.value)}
              required
              disabled={saving}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">País</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={country_id}
              onChange={(e) => setCountryId(e.target.value)}
              required
              disabled={saving}
            >
              <option value="">Seleccione el país</option>
              {countries.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
                
              ))}
            </select>
          </div>
      <div className="space-y-1">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActive(a => !a)}
                disabled={saving}
                className="flex items-center gap-2 px-3 py-2 rounded bg-white transition-colors focus:outline-none disabled:opacity-50"
                aria-pressed={active}
                aria-label={active ? 'Desactivar división' : 'Activar división'}
                title={active ? 'Desactivar división' : 'Activar división'}
              >
                {active ? <ToggleRight className="h-6 w-6 text-green-600" /> : <ToggleLeft className="h-6 w-6 text-gray-400" />}
                <span
                  className={`inline-block text-[13px] font-semibold px-3 py-1 rounded-full border text-center align-middle transition-colors duration-200 min-w-[70px] ${active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-gray-100 text-gray-600 border-gray-300'}`}
                >
                  {active ? 'Activa' : 'Inactiva'}
                </span>
              </button>
            </div>
          </div>
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-sm rounded border bg-white hover:bg-gray-50 disabled:opacity-50"
            >Cancelar</button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {saving && <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />}
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};