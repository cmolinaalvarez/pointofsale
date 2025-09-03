import React from "react";

interface ConfirmDialogProps {
  open: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ open, title, message, confirmText = "Sí", cancelText = "Cancelar", onConfirm, onCancel }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6">
        {title && <h3 className="text-lg font-semibold mb-2">{title}</h3>}
        <p className="mb-6 text-gray-700">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded border bg-white hover:bg-gray-50 text-gray-700"
          >{cancelText}</button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700"
          >{confirmText}</button>
        </div>
      </div>
    </div>
  );
};
