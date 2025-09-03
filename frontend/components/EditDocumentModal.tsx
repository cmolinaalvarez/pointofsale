import React, { useEffect, useState } from 'react';
import { Document, DocumentTypeEnum } from '@/app/types/document';
import { ToggleLeft, ToggleRight } from 'lucide-react';

interface EditDocumentModalProps {
  document: Document | null;
  documentTypeEnum: DocumentTypeEnum;
  onClose: () => void;
  onSave: (data: { 
    id: string; 
    code: string;
    name: string; 
    description?: string; 
    prefix: string;
    document_type: string;
    active: boolean 
  }) => Promise<void> | void;
  saving?: boolean;
}

export const EditDocumentModal: React.FC<EditDocumentModalProps> = ({ 
  document, 
  documentTypeEnum,
  onClose, 
  onSave, 
  saving = false 
}) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [prefix, setPrefix] = useState('');
  const [document_type, setDocumentType] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [active, setActive] = useState<boolean>(true);

  const documentTypeOptions = Object.entries(documentTypeEnum).map(([value, label]) => ({
    value,
    label
  }));

  useEffect(() => {
    if (document) {    
      console.log('Valor actual:', document.document_type);
      console.log('Opciones:', documentTypeOptions);  
      setCode(document.code || '');
      setName(document.name || '');      
      setDescription(document.description || '');
      setPrefix(document.prefix || '');
      // Buscar el value correspondiente al label recibido
      let initialDocumentType = '';
      if (document.document_type) {
        // Buscar en las opciones el value cuyo label coincide con document.document_type
        const found = documentTypeOptions.find(opt => opt.label === document.document_type);
        initialDocumentType = found ? found.value : document.document_type;
      }
      setDocumentType(initialDocumentType);
      setActive(!!document.active);
      setLocalError(null);
    }
  }, [document]);

  if (!document) return null;

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
    if (!document_type.trim()) {
      setLocalError('El tipo de documento es obligatorio');
      return;
    }   
    const payload = {
      id: document.id,
      code: code.trim(),
      name: name.trim(),
      description: description.trim() || undefined,
      prefix: prefix.trim(),
      document_type: document_type.trim(),
      active: Boolean(active)
    };
    
    await onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white w-full max-w-lg rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Editar documento</h2>
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
            <label className="text-xs font-medium text-gray-600">Descripción</label>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm resize-y min-h-[80px] focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={saving}
            />
          </div>
          
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600">Tipo de documento</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              value={document_type}
              onChange={(e) => setDocumentType(e.target.value)}
              required
              disabled={saving}
            >
              <option value="">Seleccionar tipo</option>
              {documentTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
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
                aria-label={active ? 'Desactivar documento' : 'Activar documento'}
                title={active ? 'Desactivar documento' : 'Activar documento'}
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
            >
              Cancelar
            </button>
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