import React, { useState, useEffect } from 'react';
import { ConceptTypeEnum } from '@/app/types/concept';
import { ToggleLeft, ToggleRight } from 'lucide-react';

interface CreateConceptModalProps {
  open: boolean;
  conceptTypeEnum: ConceptTypeEnum;
  onClose: () => void;
  onSave: (data: { 
    code: string; 
    name: string; 
    description?: string; 
    concept_type: string;
    debit_account_id: string; // ✅ Nuevo campo
    credit_account_id: string; // ✅ Nuevo campo
    active: boolean 
  }) => Promise<void> | void;
  saving?: boolean;
  accounts?: Array<{ id: string; name: string; code: string }>;
  loadingAccounts?: boolean;
}

export const CreateConceptModal: React.FC<CreateConceptModalProps> = ({ 
  open, 
  conceptTypeEnum,
  onClose, 
  onSave, 
  saving = false,
  accounts = [],
  loadingAccounts = false
}) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [concept_type, setConceptType] = useState('');
  const [debit_account_id, setDebitAccountId] = useState(''); // ✅ Nuevo estado
  const [debit_account_code, setDebitAccountCode] = useState('');
  const [credit_account_id, setCreditAccountId] = useState(''); // ✅ Nuevo estado
  const [credit_account_code, setCreditAccountCode] = useState('');
  const [active, setActive] = useState(true);
  const [localError, setLocalError] = useState<string | null>(null);

  const conceptTypeOptions = Object.entries(conceptTypeEnum).map(([value, label]) => ({
    value,
    label
  }));

  useEffect(() => {
    if (open) {
      setActive(true);
      setConceptType('');
      setDebitAccountId('');
      setCreditAccountId('');
    }
  }, [open]);

  if (!open) return null;

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
    if (!concept_type.trim()) {
      setLocalError('El tipo de concepto es obligatorio');
      return;
    }
    if (!debit_account_id.trim()) {
      setLocalError('La cuenta de débito es obligatoria');
      return;
    }
    if (!credit_account_id.trim()) {
      setLocalError('La cuenta de crédito es obligatoria');
      return;
    }
    
    await onSave({
      code: code.trim(),
      name: name.trim(),
      description: description.trim() || undefined,
      concept_type: concept_type.trim(),
      debit_account_id: debit_account_id.trim(), // ✅ Incluir nuevo campo
      credit_account_id: credit_account_id.trim(), // ✅ Incluir nuevo campo
      active: Boolean(active)
    });
    
    // Resetear formulario
    setCode('');
    setName('');
    setDescription('');
    setConceptType('');
    setDebitAccountId('');
    setCreditAccountId('');
    setActive(true);
    setLocalError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white w-full max-w-lg rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Nuevo Concepto</h2>
          <button onClick={onClose} aria-label="Cerrar" className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {localError && <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-2 rounded">{localError}</div>}
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Código</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none bg-green-50 text-green-800 font-bold placeholder:text-green-300"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              disabled={saving}
              maxLength={50}
              placeholder="Código único"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Nombre</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={saving}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Descripción</label>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm resize-y min-h-[80px] focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={saving}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Tipo de concepto</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={concept_type}
              onChange={e => setConceptType(e.target.value)}
              required
              disabled={saving}
            >
              <option value="">Seleccionar tipo</option>
              {conceptTypeOptions.map(option => (
                <option key={option.value} value={option.value}>{String(option.label)}</option>
              ))}
            </select>
          </div>
          {/* ✅ Selects para elegir la cuenta de débito y crédito */}
          <div className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600">Cuenta Débito</label>
              <div className="flex items-center justify-between w-full">
                <select
                  className="border rounded px-3 py-2 text-sm focus:outline-none"
                  style={{ width: '45%' }}
                  value={debit_account_id}
                  onChange={e => {
                    setDebitAccountId(e.target.value);
                    const cuenta = accounts.find(a => a.id === e.target.value);
                    setDebitAccountCode(cuenta ? cuenta.code : '');
                  }}
                  required
                  disabled={saving || loadingAccounts}
                >
                  <option value="">{loadingAccounts ? 'Cargando cuentas...' : 'Seleccionar cuenta'}</option>
                  {accounts.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>{cuenta.name}</option>
                  ))}
                </select>
                <span className="text-xs font-semibold text-gray-700 min-w-[160px] text-right block">
                  <span className="bg-green-50 text-green-800 font-bold px-2 py-1 rounded">
                    {debit_account_id ? debit_account_code : 'Seleccione cuenta débito'}
                  </span>
                </span>
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600">Cuenta Crédito</label>
              <div className="flex items-center justify-between w-full">
                <select
                  className="border rounded px-3 py-2 text-sm focus:outline-none"
                  style={{ width: '45%' }}
                  value={credit_account_id}
                  onChange={e => {
                    setCreditAccountId(e.target.value);
                    const cuenta = accounts.find(a => a.id === e.target.value);
                    setCreditAccountCode(cuenta ? cuenta.code : '');
                  }}
                  required
                  disabled={saving || loadingAccounts}
                >
                  <option value="">{loadingAccounts ? 'Cargando cuentas...' : 'Seleccionar cuenta'}</option>
                  {accounts.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>{cuenta.name}</option>
                  ))}
                </select>
                <span className="text-xs font-semibold text-gray-700 min-w-[160px] text-right block">
                  <span className="bg-green-50 text-green-800 font-bold px-2 py-1 rounded">
                    {credit_account_id ? credit_account_code : 'Seleccione cuenta crédito'}
                  </span>
                </span>
              </div>
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActive(a => !a)}
                disabled={saving}
                className="flex items-center gap-2 px-3 py-2 rounded bg-white transition-colors focus:outline-none disabled:opacity-50"
                aria-pressed={active}
                aria-label={active ? 'Desactivar concepto' : 'Activar concepto'}
                title={active ? 'Desactivar concepto' : 'Activar concepto'}
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
              className="px-4 py-2 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
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