"use client";
import { useProduct } from "@/hooks/useProduct";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useState } from "react";

export default function ProductsPage() {
  const [isClient, setIsClient] = useState(false);
  // Limpieza: removido estado de diagnóstico
  const { token } = useAuth();
  const { products, loading, error, refetch, clearError, page, pageSize, total, totalPages, setPage, setPageSize } = useProduct(token);

  // Verificar qué endpoints están disponibles
  // Métodos de diagnóstico eliminados

  useEffect(() => {
    setIsClient(true);
  // Inicialización simplificada
  console.log("🏠 ProductsPage montado - modo limpio");
  }, [token]);

  useEffect(() => {
    console.log("📊 Productos actualizados:", products);
    console.log("📊 Cantidad:", products.length);
  }, [products]);

  useEffect(() => {
    console.log("⏳ Loading:", loading);
  }, [loading]);

  useEffect(() => {
    console.log("❌ Error:", error);
  }, [error]);

  if (!isClient) return null;

  if (!token) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-red-600">No Token</h1>
        <p>No se encontró token de autenticación</p>
        <button 
          onClick={() => window.location.href = '/login'}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded"
        >
          Ir a Login
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Productos</h1>
      <div className="mb-4 flex flex-wrap gap-4 items-center text-sm">
        <div className="flex gap-2">
          <button onClick={() => refetch()} className="bg-blue-600 text-white px-3 py-1 rounded text-sm" title="Refrescar">↻</button>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={() => setPage(1)} disabled={page===1 || loading}>&laquo;</button>
          <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={() => setPage(page-1)} disabled={page===1 || loading}>&lsaquo;</button>
          <span>Página {page} / {totalPages}</span>
          <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={() => setPage(page+1)} disabled={page===totalPages || loading}>&rsaquo;</button>
          <button className="px-2 py-1 border rounded disabled:opacity-40" onClick={() => setPage(totalPages)} disabled={page===totalPages || loading}>&raquo;</button>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="pageSizeP" className="text-gray-600">Filas:</label>
          <select id="pageSizeP" className="border rounded px-2 py-1" value={pageSize} onChange={(e)=> { setPageSize(Number(e.target.value)); setPage(1); }} disabled={loading}>
            {[5,10,20,50].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="text-gray-500">Mostrando {(page-1)*pageSize + 1}-{Math.min(page*pageSize, total || ((page-1)*pageSize + products.length))}</div>
      </div>

  {/* Mensaje de error simple */}

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p>Cargando productos...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
          <h3 className="font-bold text-red-800">Error:</h3>
          <p className="text-red-700">{error}</p>
          <button 
            onClick={() => {
              clearError();
              refetch();
            }}
            className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm"
          >
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className="bg-white shadow rounded">
          <div className="px-4 py-3 border-b">
            <h3 className="font-semibold">Lista de Productos ({products.length}{total ? `/ ${total}`: ''})</h3>
          </div>
          <div className="p-4">
            {products.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No hay productos disponibles</p>
            ) : (
              <div className="space-y-2">
                {products.map((product: any, index: number) => (
                  <div key={product.id || index} className="border rounded p-3">
                    <p><strong>ID:</strong> {product.id}</p>
                    <p><strong>Nombre:</strong> {product.name || 'Sin nombre'}</p>
                    <p><strong>Precio:</strong> ${product.price || '0.00'}</p>
                    <p><strong>Stock:</strong> {product.stock || 'N/A'}</p>
                    <details className="mt-2">
                      <summary className="cursor-pointer text-blue-600">Ver datos completos</summary>
                      <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                        {JSON.stringify(product, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

  {/* Se eliminó bloque de debug extendido */}
    </div>
  );
}