'use client';

import { useState, useEffect } from 'react';
import { productService } from '@/app/services/productService';
import { authService } from '@/app/services/authService';

export default function DashboardPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadProducts = async () => {
    const token = authService.getToken();
    if (!token) {
      setError('No hay token de autenticación');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      console.log('🔍 Cargando productos con token...');
      console.log('🔑 Token preview:', token.substring(0, 30) + '...');
      
      // Usar parámetros por defecto similares a la API
      const data = await productService.getProducts(token, {
        skip: 0,
        limit: 100,
        active: true
      });
      
      console.log('✅ Productos cargados:', data);
      setProducts(Array.isArray(data) ? data : data.items || []);
    } catch (error: any) {
      console.error('❌ Error cargando productos:', error);
      setError(error.message || 'Error al cargar productos');
      
      // Si el token es inválido, redirigir al login
      if (error.message.includes('Token') || error.message.includes('401')) {
        authService.logout();
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const testBackendConnection = async () => {
    try {
      console.log('🔗 Probando conexión con backend...');
      const response = await fetch('http://localhost:8000/docs');
      console.log('📡 Response status:', response.status);
      if (response.ok) {
        window.open('http://localhost:8000/docs', '_blank');
      }
    } catch (error) {
      console.error('❌ Error conectando con backend:', error);
      alert('No se puede conectar con el backend en http://localhost:8000');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Productos</h1>
              <p className="text-sm text-gray-600 mt-1">
                Estado del Backend: {loading ? 'Cargando...' : error ? 'Error' : 'Conectado'}
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={loadProducts}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Cargando...' : 'Recargar'}
              </button>
              <button
                onClick={testBackendConnection}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Abrir Docs API
              </button>
            </div>
          </div>

          {/* Debug Info */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-yellow-800 mb-2">🔧 Debug Info:</h3>
            <div className="text-sm text-yellow-700 space-y-1">
              <p><strong>URL de API:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}</p>
              <p><strong>URL Real Backend:</strong> http://localhost:8000</p>
              <p><strong>Endpoint:</strong> /products/</p>
              <p><strong>Token presente:</strong> {authService.getToken() ? 'Sí' : 'No'}</p>
              <p><strong>Token preview:</strong> {authService.getToken()?.substring(0, 20) + '...' || 'N/A'}</p>
              <p><strong>Productos cargados:</strong> {products.length}</p>
              <p><strong>Estado:</strong> {loading ? 'Cargando' : error ? `Error: ${error}` : 'OK'}</p>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">Error:</span> {error}
              </div>
            </div>
          )}

          {/* Products List */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Lista de Productos ({products.length})
            </h2>
            
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <span className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mr-4"></span>
                <span className="text-blue-700 font-semibold text-lg">Cargando productos...</span>
              </div>
            ) : products.length === 0 ? (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No hay productos</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {error ? 'Error al cargar productos' : 'No hay productos disponibles'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.map((product: any, index) => (
                  <div key={product.id || index} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900">{product.name || product.nombre || 'Sin nombre'}</h3>
                    <p className="text-sm text-gray-600 mt-1">{product.description || product.descripcion || 'Sin descripción'}</p>
                    <p className="text-lg font-semibold text-green-600 mt-2">
                      ${product.price || product.precio || '0.00'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Help Section */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-800 mb-2">💡 Para verificar la ruta correcta:</h3>
            <div className="text-sm text-blue-700 space-y-1">
              <p>1. Abre: <a href="http://localhost:8000/docs" target="_blank" className="underline">http://localhost:8000/docs</a> (FastAPI docs)</p>
              <p>2. Busca los endpoints de productos</p>
              <p>3. La ruta debería ser: <code className="bg-blue-100 px-1 rounded">/products</code> o <code className="bg-blue-100 px-1 rounded">/api/products</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}