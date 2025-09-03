'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/app/services/authService';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLdapLoading, setIsLdapLoading] = useState(false);
  const router = useRouter();
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      router.replace('/');
    }
  }, [token, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const result = await authService.login(formData.email, formData.password);
      console.log('Login successful:', result);
      router.push('/');
    } catch (error: any) {
      console.error('Login failed:', error);
      setError(error.message || 'Error al iniciar sesión');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLdapLogin = async () => {
    setIsLdapLoading(true);
    setError('');
    
    try {
      // Aquí iría tu lógica para login con LDAP
      console.log('Intentando login LDAP');
      // Simulamos un delay para demostrar el loading
      await new Promise(resolve => setTimeout(resolve, 2000));
      setError('Login LDAP no implementado aún');
    } catch (error: any) {
      console.error('LDAP login failed:', error);
      setError(error.message || 'Error al iniciar sesión con LDAP');
    } finally {
      setIsLdapLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center p-4"
      style={{ 
        backgroundImage: 'url(/assets/images/fondo.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Logo y texto en la esquina superior izquierda */}
      <div className="absolute top-6 left-6 z-20 flex items-center space-x-4">
        <img 
          src="/assets/images/logo.png" 
          alt="CAMA Logo" 
          className="h-12 w-auto"
        />
        <h1 className="text-white text-2xl font-bold drop-shadow-2xl shadow-black">
          Punto de Venta
        </h1>
      </div>

      <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl max-w-md w-full mx-auto relative z-10 border border-white/20">
        {/* Header moderno */}
        <div className="px-8 py-6 text-center border-b border-gray-100">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Bienvenido</h2>
          <p className="text-gray-600 text-sm">Inicia sesión para continuar</p>
        </div>
        
        <div className="px-8 py-6">
          {/* Selector de método de autenticación */}
          <div className="flex space-x-2 mb-6 bg-gray-100 rounded-lg p-1">
            <button 
              className="flex-1 py-2 px-4 text-sm font-medium rounded-md bg-white text-indigo-600 shadow-sm transition-all"
              disabled={isLoading || isLdapLoading}
            >
              Credenciales
            </button>
            <button 
              className="flex-1 py-2 px-4 text-sm font-medium rounded-md text-gray-500 hover:text-gray-700 transition-all disabled:opacity-50"
              disabled={isLoading || isLdapLoading}
              onClick={handleLdapLogin}
            >
              {isLdapLoading ? 'Cargando...' : 'LDAP'}
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  Correo electrónico
                </label>
                <div className="relative">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    disabled={isLoading || isLdapLoading}
                    className="w-full px-4 py-3 pl-11 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-200 bg-gray-50 focus:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="ejemplo@correo.com"
                  />
                  <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                  </svg>
                </div>
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    disabled={isLoading || isLdapLoading}
                    className="w-full px-4 py-3 pl-11 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-200 bg-gray-50 focus:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="••••••••••••"
                  />
                  <svg className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-end text-sm">
              <a href="#" className="text-indigo-600 hover:text-indigo-500 font-medium disabled:opacity-50 disabled:cursor-not-allowed" disabled={isLoading || isLdapLoading}>
                ¿Olvidaste tu contraseña?
              </a>
            </div>
            <div className="space-y-3">
              <button
                type="submit"
                disabled={isLoading || isLdapLoading}
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 transform hover:scale-[1.02] shadow-lg"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Iniciando sesión...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    Iniciar Sesión
                  </div>
                )}
              </button>
              <button
                type="button"
                onClick={handleLdapLogin}
                disabled={isLoading || isLdapLoading}
                className="w-full bg-white border-2 border-gray-300 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 transform hover:scale-[1.02]"
              >
                {isLdapLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Conectando LDAP...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    Ingresar con LDAP
                  </div>
                )}
              </button>
            </div>
          </form>
          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-xs text-gray-500">© 2024 CAMA. Todos los derechos reservados.</p>
          </div>
        </div>
      </div>

      {/* Overlay de loading global */}
      {(isLoading || isLdapLoading) && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 shadow-xl flex items-center space-x-3">
            <svg className="animate-spin h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-gray-700">Procesando...</span>
          </div>
        </div>
      )}
    </div>
  );
}