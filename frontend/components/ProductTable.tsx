import { Product } from '@/app/types/product';

interface ProductTableProps {
  products: Product[];
  onEdit?: (product: Product) => void;
  onDelete?: (id: number) => void;
  loading?: boolean;
}

export const ProductTable: React.FC<ProductTableProps> = ({
  products,
  onEdit,
  onDelete,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded mb-4"></div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="min-w-full table-auto border border-gray-200">
        <thead>
          <tr className="bg-gradient-to-r from-blue-500 to-blue-700">
            <th className="px-4 py-3 text-left text-white font-bold uppercase tracking-wider">Nombre</th>
            <th className="px-4 py-3 text-left text-white font-bold uppercase tracking-wider">Precio</th>
            <th className="px-4 py-3 text-left text-white font-bold uppercase tracking-wider">Stock</th>
            <th className="px-4 py-3 text-left text-white font-bold uppercase tracking-wider">Categoría</th>
            {(onEdit || onDelete) && (
              <th className="px-4 py-3 text-left text-white font-bold uppercase tracking-wider">Acciones</th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {products.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center py-8 text-gray-500 text-lg">
                <span role="img" aria-label="Caja vacía">📦</span> No existen productos disponibles
              </td>
            </tr>
          ) : (
            products.map((product) => (
              <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{product.name}</td>
                <td className="px-4 py-3 text-sm text-gray-700">${product.price.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{product.stock || 'N/A'}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{product.category || 'Sin categoría'}</td>
                {(onEdit || onDelete) && (
                  <td className="px-4 py-3 text-sm font-medium space-x-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(product)}
                        className="text-blue-600 hover:text-blue-900 transition-colors"
                      >
                        Editar
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(product.id)}
                        className="text-red-600 hover:text-red-900 transition-colors"
                      >
                        Eliminar
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
