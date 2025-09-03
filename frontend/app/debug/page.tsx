'use client';

import { useState } from 'react';
import { authService } from '@/app/services/authService';

export default function DebugPage() {
  const [results, setResults] = useState<any>({});
  const [testCredentials, setTestCredentials] = useState({
    email: 'test@example.com',
    password: 'test123'
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  const backendUrl = apiUrl.replace('/api', '');

  const testDirectLogin = async () => {
    console.log('🔐 Testing direct login...');
    
    try {
      const formData = new FormData();
      formData.append('username', testCredentials.email);
      formData.append('password', testCredentials.password);

      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        body: formData,
      });

      const text = await response.text();
      
      setResults(prev => ({
        ...prev,
        'Direct Login Test (FormData)': {
          status: response.status,
          ok: response.ok,
          url: `${backendUrl}/auth/login`,
          method: 'POST (FormData)',
          credentials: `${testCredentials.email} / ${testCredentials.password}`,
          response: text.substring(0, 500),
          headers: Object.fromEntries(response.headers.entries()),
        }
      }));

    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'Direct Login Test (FormData)': {
          error: error.message,
          status: 'NETWORK_ERROR'
        }
      }));
    }
  };

  const testUrlEncodedLogin = async () => {
    console.log('🔐 Testing URL encoded login...');
    
    try {
      const params = new URLSearchParams();
      params.append('username', testCredentials.email);
      params.append('password', testCredentials.password);

      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: params,
      });

      const text = await response.text();
      
      setResults(prev => ({
        ...prev,
        'URL Encoded Login Test': {
          status: response.status,
          ok: response.ok,
          url: `${backendUrl}/auth/login`,
          method: 'POST (URLSearchParams)',
          credentials: `${testCredentials.email} / ${testCredentials.password}`,
          response: text.substring(0, 500),
          contentType: 'application/x-www-form-urlencoded',
        }
      }));

    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'URL Encoded Login Test': {
          error: error.message,
          status: 'NETWORK_ERROR'
        }
      }));
    }
  };

  const testJsonLogin = async () => {
    console.log('🔐 Testing JSON login...');
    
    try {
      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: testCredentials.email,
          password: testCredentials.password
        }),
      });

      const text = await response.text();
      
      setResults(prev => ({
        ...prev,
        'JSON Login Test (username)': {
          status: response.status,
          ok: response.ok,
          url: `${backendUrl}/auth/login`,
          method: 'POST (JSON)',
          payload: `{"username": "${testCredentials.email}", "password": "***"}`,
          response: text.substring(0, 500),
        }
      }));
    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'JSON Login Test (username)': {
          error: error.message,
          status: 'NETWORK_ERROR'
        }
      }));
    }
  };

  const testJsonEmailLogin = async () => {
    console.log('🔐 Testing JSON login with email field...');
    
    try {
      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: testCredentials.email,
          password: testCredentials.password
        }),
      });

      const text = await response.text();
      
      setResults(prev => ({
        ...prev,
        'JSON Login Test (email)': {
          status: response.status,
          ok: response.ok,
          url: `${backendUrl}/auth/login`,
          method: 'POST (JSON)',
          payload: `{"email": "${testCredentials.email}", "password": "***"}`,
          response: text.substring(0, 500),
        }
      }));
    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'JSON Login Test (email)': {
          error: error.message,
          status: 'NETWORK_ERROR'
        }
      }));
    }
  };

  const testEmailVariants = async () => {
    console.log('🔐 Testing email vs username variants...');
    
    const variants = [
      { field: 'username', value: testCredentials.email },
      { field: 'email', value: testCredentials.email },
    ];

    for (const variant of variants) {
      try {
        const params = new URLSearchParams();
        params.append(variant.field, variant.value);
        params.append('password', testCredentials.password);

        const response = await fetch(`${backendUrl}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: params,
        });

        const text = await response.text();
        
        setResults(prev => ({
          ...prev,
          [`Login Test (${variant.field})`]: {
            status: response.status,
            ok: response.ok,
            method: `POST (${variant.field} field)`,
            response: text.substring(0, 300),
          }
        }));

      } catch (error: any) {
        setResults(prev => ({
          ...prev,
          [`Login Test (${variant.field})`]: {
            error: error.message,
            status: 'NETWORK_ERROR'
          }
        }));
      }
    }
  };

  const checkBackendStatus = async () => {
    const endpoints = [
      { name: 'Backend Root', url: backendUrl },
      { name: 'Auth Endpoint', url: `${backendUrl}/auth/login`, method: 'GET' },
      { name: 'Docs', url: `${backendUrl}/docs` },
      { name: 'OpenAPI', url: `${backendUrl}/openapi.json` },
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint.url, {
          method: endpoint.method || 'GET',
        });

        const text = await response.text();
        
        setResults(prev => ({
          ...prev,
          [endpoint.name]: {
            status: response.status,
            ok: response.ok,
            url: endpoint.url,
            response: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
          }
        }));
      } catch (error: any) {
        setResults(prev => ({
          ...prev,
          [endpoint.name]: {
            error: error.message,
            status: 'NETWORK_ERROR',
            url: endpoint.url,
          }
        }));
      }
    }
  };

  const testAuthServiceLogin = async () => {
    console.log('🔐 Testing AuthService.login directly...');
    
    try {
      setResults(prev => ({
        ...prev,
        'AuthService Test': { status: 'LOADING', message: 'Testing...' }
      }));

      const result = await authService.login(testCredentials.email, testCredentials.password);
      
      setResults(prev => ({
        ...prev,
        'AuthService Test': {
          status: 'SUCCESS',
          ok: true,
          message: 'Login successful!',
          data: { 
            hasToken: !!result.access_token,
            tokenPreview: result.access_token?.substring(0, 20) + '...',
            user: result.user 
          }
        }
      }));

    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'AuthService Test': {
          status: 'ERROR',
          ok: false,
          error: error.message,
          stack: error.stack
        }
      }));
    }
  };

  const testDirectApiCall = async () => {
    console.log('🔐 Testing direct API call...');
    
    try {
      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: testCredentials.email,
          password: testCredentials.password
        }),
      });

      const text = await response.text();
      
      setResults(prev => ({
        ...prev,
        'Direct API Test': {
          status: response.status,
          ok: response.ok,
          url: `${backendUrl}/auth/login`,
          method: 'POST (JSON)',
          payload: `{"email": "${testCredentials.email}", "password": "***"}`,
          response: text,
          headers: Object.fromEntries(response.headers.entries()),
        }
      }));

    } catch (error: any) {
      setResults(prev => ({
        ...prev,
        'Direct API Test': {
          error: error.message,
          status: 'NETWORK_ERROR'
        }
      }));
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">🔧 Debug Login - Diagnóstico Completo</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <h3 className="font-bold mb-2">📋 Configuración:</h3>
          <p><strong>Frontend API URL:</strong> {apiUrl}</p>
          <p><strong>Backend URL Real:</strong> {backendUrl}</p>
          <p><strong>Login Endpoint:</strong> {backendUrl}/auth/login</p>
        </div>

        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="font-bold mb-2">🔑 Credenciales:</h3>
          <input
            type="email"
            placeholder="Email"
            value={testCredentials.email}
            onChange={(e) => setTestCredentials(prev => ({...prev, email: e.target.value}))}
            className="w-full p-2 border rounded mb-2 text-sm"
          />
          <input
            type="password"
            placeholder="Password"
            value={testCredentials.password}
            onChange={(e) => setTestCredentials(prev => ({...prev, password: e.target.value}))}
            className="w-full p-2 border rounded text-sm"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={checkBackendStatus}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          🔍 Verificar Backend
        </button>
        
        <button
          onClick={testDirectLogin}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          🔐 Test Login (FormData)
        </button>
        
        <button
          onClick={testUrlEncodedLogin}
          className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700"
        >
          🌐 Test URLEncoded
        </button>

        <button
          onClick={testJsonLogin}
          className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700"
        >
          📝 Test Login (JSON)
        </button>

        <button
          onClick={testJsonEmailLogin}
          className="bg-pink-600 text-white px-4 py-2 rounded hover:bg-pink-700"
        >
          📧 Test JSON (email)
        </button>

        <button
          onClick={testEmailVariants}
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          📧 Test Email/Username
        </button>

        <button
          onClick={testAuthServiceLogin}
          className="bg-green-700 text-white px-4 py-2 rounded hover:bg-green-800"
        >
          🔐 Test AuthService
        </button>
        
        <button
          onClick={testDirectApiCall}
          className="bg-blue-700 text-white px-4 py-2 rounded hover:bg-blue-800"
        >
          📡 Test Direct API
        </button>

        <button
          onClick={() => window.open(`${backendUrl}/docs`, '_blank')}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
        >
          📚 Open API Docs
        </button>

        <button
          onClick={() => setResults({})}
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
        >
          🧹 Limpiar
        </button>
      </div>

      {/* Resultados */}
      {Object.keys(results).length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">📊 Resultados:</h2>
          
          {Object.entries(results).map(([testName, result]: [string, any]) => (
            <div key={testName} className={`p-4 border rounded ${
              result.ok ? 'border-green-500 bg-green-50' : 
              result.error || result.status === 'ERROR' ? 'border-red-500 bg-red-50' : 
              'border-yellow-500 bg-yellow-50'
            }`}>
              <h3 className="font-bold mb-2">
                {testName} {result.ok ? '✅' : result.error ? '❌' : '⚠️'}
              </h3>
              
              <div className="text-sm space-y-2">
                {result.status && <p><strong>Status:</strong> {result.status}</p>}
                {result.error && <p className="text-red-600"><strong>Error:</strong> {result.error}</p>}
                {result.message && <p><strong>Message:</strong> {result.message}</p>}
                
                {result.response && (
                  <div>
                    <strong>Response:</strong>
                    <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-x-auto max-h-32">
                      {result.response}
                    </pre>
                  </div>
                )}
                
                {result.data && (
                  <div>
                    <strong>Data:</strong>
                    <pre className="bg-gray-100 p-2 rounded mt-1 text-xs">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded">
        <h3 className="font-bold mb-2">💡 Pasos para debugear:</h3>
        <ol className="list-decimal list-inside text-sm space-y-1">
          <li>Verificar que el backend esté corriendo en puerto 8000</li>
          <li>Abrir la documentación en <code>/docs</code> para ver endpoints disponibles</li>
          <li>Probar login con FormData (estándar OAuth2)</li>
          <li>Verificar las credenciales exactas que funcionan en Postman</li>
          <li>Revisar la consola del navegador para errores detallados</li>
        </ol>
      </div>
    </div>
  );
}
