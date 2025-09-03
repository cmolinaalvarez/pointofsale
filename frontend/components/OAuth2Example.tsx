'use client';

import { useState, useEffect } from 'react';
import { oauth2Service } from '../app/services/oauth2Service';

interface User {
  id: string;
  email: string;
  username: string;
  active: boolean;
  superuser: boolean;
}

export default function OAuth2Example() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [scopes, setScopes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estados del formulario
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [requestedScopes, setRequestedScopes] = useState('read write');

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = () => {
    const currentToken = oauth2Service.getCurrentToken();
    const tokenScopes = oauth2Service.getTokenScopes();
    const isExpired = oauth2Service.isTokenExpired();

    if (currentToken && !isExpired) {
      setIsAuthenticated(true);
      setToken(currentToken);
      setScopes(tokenScopes);
      fetchUserInfo(currentToken);
    } else {
      setIsAuthenticated(false);
      setUser(null);
      setToken(null);
      setScopes([]);
    }
  };

  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await fetch('http://localhost:8000/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (err) {
      console.error('Error fetching user info:', err);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await oauth2Service.login(email, password, requestedScopes);
      
      console.log('✅ Login exitoso:', response);
      checkAuthStatus();
      
      // Limpiar formulario
      setEmail('');
      setPassword('');
      
    } catch (err: any) {
      setError(err.message || 'Error de autenticación');
      console.error('❌ Login failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await oauth2Service.logout();
      checkAuthStatus();
    } catch (err) {
      console.error('Error during logout:', err);
    }
  };

  const testProtectedEndpoint = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/products', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Protected endpoint response:', data);
        alert('✅ Acceso autorizado a productos!');
      } else {
        const errorData = await response.json();
        setError(`Error ${response.status}: ${errorData.detail}`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h1 className="text-2xl font-bold text-blue-800 mb-2">
          🔐 Sistema OAuth2 Demo
        </h1>
        <p className="text-blue-600">
          Ejemplo completo de autenticación OAuth2 con scopes y permisos
        </p>
      </div>

      {/* Estado de Autenticación */}
      <div className="bg-white border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-3">📊 Estado de Autenticación</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="font-medium">Estado:</p>
            <span className={`px-3 py-1 rounded-full text-sm ${
              isAuthenticated 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {isAuthenticated ? '✅ Autenticado' : '❌ No autenticado'}
            </span>
          </div>
          
          <div>
            <p className="font-medium">Scopes:</p>
            <div className="flex flex-wrap gap-1">
              {scopes.map((scope) => (
                <span key={scope} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  {scope}
                </span>
              ))}
            </div>
          </div>
        </div>

        {token && (
          <div className="mt-3">
            <p className="font-medium">Token:</p>
            <code className="text-xs bg-gray-100 p-2 rounded block break-all">
              {token.substring(0, 100)}...
            </code>
          </div>
        )}
      </div>

      {/* Información del Usuario */}
      {user && (
        <div className="bg-white border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">👤 Información del Usuario</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="font-medium">Email:</p>
              <p className="text-gray-600">{user.email}</p>
            </div>
            <div>
              <p className="font-medium">Username:</p>
              <p className="text-gray-600">{user.username}</p>
            </div>
            <div>
              <p className="font-medium">Activo:</p>
              <span className={`px-2 py-1 rounded text-sm ${
                user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {user.active ? 'Sí' : 'No'}
              </span>
            </div>
            <div>
              <p className="font-medium">Superusuario:</p>
              <span className={`px-2 py-1 rounded text-sm ${
                user.superuser ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {user.superuser ? 'Sí' : 'No'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Formulario de Login */}
      {!isAuthenticated && (
        <div className="bg-white border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">🔑 Iniciar Sesión</h2>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block font-medium mb-1">Email:</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="usuario@ejemplo.com"
                required
              />
            </div>
            
            <div>
              <label className="block font-medium mb-1">Contraseña:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="tu-contraseña"
                required
              />
            </div>
            
            <div>
              <label className="block font-medium mb-1">Scopes (permisos):</label>
              <input
                type="text"
                value={requestedScopes}
                onChange={(e) => setRequestedScopes(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="read write admin"
              />
              <p className="text-sm text-gray-500 mt-1">
                Separar con espacios: read, write, delete, admin
              </p>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Autenticando...' : 'Iniciar Sesión'}
            </button>
          </form>
        </div>
      )}

      {/* Acciones */}
      {isAuthenticated && (
        <div className="bg-white border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">🛠️ Acciones</h2>
          
          <div className="flex flex-wrap gap-3">
            <button
              onClick={testProtectedEndpoint}
              disabled={loading}
              className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              🔒 Probar Endpoint Protegido
            </button>
            
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700"
            >
              🚪 Cerrar Sesión
            </button>
            
            <button
              onClick={checkAuthStatus}
              className="bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700"
            >
              🔄 Actualizar Estado
            </button>
          </div>
        </div>
      )}

      {/* Errores */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-semibold text-red-800">❌ Error</h3>
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Información de Desarrollo */}
      <div className="bg-gray-50 border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-3">🔧 Información de Desarrollo</h2>
        
        <div className="text-sm space-y-2">
          <p><strong>Backend URL:</strong> http://localhost:8000</p>
          <p><strong>Client ID:</strong> frontend</p>
          <p><strong>Token Endpoint:</strong> /auth/token</p>
          <p><strong>Me Endpoint:</strong> /auth/me</p>
          <p><strong>OAuth2 Info:</strong> /auth/oauth2/info</p>
        </div>
        
        <div className="mt-4">
          <h3 className="font-semibold mb-2">Scopes Disponibles:</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><code>read</code> - Lectura general</div>
            <div><code>write</code> - Escritura general</div>
            <div><code>delete</code> - Eliminación</div>
            <div><code>admin</code> - Administración</div>
            <div><code>read:products</code> - Lectura productos</div>
            <div><code>write:products</code> - Escritura productos</div>
            <div><code>read:users</code> - Lectura usuarios</div>
            <div><code>write:users</code> - Escritura usuarios</div>
          </div>
        </div>
      </div>
    </div>
  );
}
