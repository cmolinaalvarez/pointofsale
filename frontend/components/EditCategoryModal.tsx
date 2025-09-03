import { Category, UpdateCategoryData } from "@/app/types/category";
import { useState, useEffect } from "react";

interface EditCategoryModalProps {
  category: Category | null;
  saving: boolean;
  onClose: () => void;
  onSave: (data: UpdateCategoryData) => void;
}

export function EditCategoryModal({ category, saving, onClose, onSave }: EditCategoryModalProps) {
  const [form, setForm] = useState<UpdateCategoryData>(
    category
      ? { ...category }
      : { id: "", code: "", name: "", description: "", active: true }
  );

  useEffect(() => {
    if (category) setForm({ ...category });
  }, [category]);

  if (!category) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-lg shadow-xl p-6 relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600" aria-label="Cerrar">✕</button>
        <h2 className="text-xl font-semibold mb-4">Editar Categoría</h2>
        <form
          onSubmit={e => {
            e.preventDefault();
            onSave(form);
          }}
          className="space-y-4"
        >
          <input type="hidden" value={form.id} />
          <div>
            <label className="block text-sm font-medium mb-1">Código</label>
            <input
              type="text"
              value={form.code}
              onChange={e => setForm(f => ({ ...f, code: e.target.value }))}
              className="border px-3 py-2 rounded w-full"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Nombre</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="border px-3 py-2 rounded w-full"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Descripción</label>
            <textarea
              value={form.description || ""}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              className="border px-3 py-2 rounded w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!form.active}
              onChange={e => setForm(f => ({ ...f, active: e.target.checked }))}
              id="active"
            />
            <label htmlFor="active" className="text-sm">Activa</label>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 text-sm">Cancelar</button>
            <button type="submit" disabled={saving} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
