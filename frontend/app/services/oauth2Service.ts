import { authService } from './authService';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const CLIENT_ID = process.env.NEXT_PUBLIC_CLIENT_ID || 'frontend';
const CLIENT_SECRET = process.env.NEXT_PUBLIC_CLIENT_SECRET || 'your-super-secret-client-secret-change-in-production';

interface OAuth2LoginData {
  username: string; // email
  password: string;
  scope?: string; // scopes opcionales
}

interface OAuth2TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  scope?: string;
}

class OAuth2Service {
  private apiUrl = API_URL;
  private clientId = CLIENT_ID;
  private clientSecret = CLIENT_SECRET;

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const url = `${this.apiUrl}${endpoint}`;
    
    console.group('🔐 OAuth2Service Request');
    console.log('📡 URL:', url);
    console.log('🔧 Method:', options.method || 'GET');
    console.log('🔑 Headers:', options.headers);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
        },
      });

      console.log('📥 Response Status:', response.status);
      console.log('📥 Response OK:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error Response:', errorText);
        console.groupEnd();
        
        if (response.status === 401) {
          throw new Error('Credenciales inválidas');
        }
        if (response.status === 400) {
          throw new Error('Solicitud incorrecta');
        }
        
        throw new Error(`HTTP ${response.status}: ${errorText || 'Error del servidor'}`);
      }

      const data = await response.json();
      console.log('✅ Response Data:', data);
      console.groupEnd();
      
      return data;
    } catch (error) {
      console.error('💥 Request Error:', error);
      console.groupEnd();
      throw error;
    }
  }

  /**
   * Obtiene un token OAuth2 usando el flujo password grant
   */
  async getToken(loginData: OAuth2LoginData): Promise<OAuth2TokenResponse> {
    console.log('🎯 OAuth2Service.getToken called');
    
    // Crear FormData para el request OAuth2
    const formData = new FormData();
    formData.append('grant_type', 'password');
    formData.append('username', loginData.username);
    formData.append('password', loginData.password);
    formData.append('client_id', this.clientId);
    formData.append('client_secret', this.clientSecret);
    
    // Agregar scopes si se especifican
    if (loginData.scope) {
      formData.append('scope', loginData.scope);
    } else {
      formData.append('scope', 'read write'); // Scopes por defecto
    }

    const response = await this.makeRequest('/auth/token', {
      method: 'POST',
      body: formData,
    });

    // Guardar el token en localStorage directamente
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      
      // Calcular fecha de expiración
      const expiresAt = new Date();
      expiresAt.setSeconds(expiresAt.getSeconds() + response.expires_in);
      localStorage.setItem('token_expires_at', expiresAt.toISOString());
      
      // Guardar scopes si están presentes
      if (response.scope) {
        localStorage.setItem('token_scopes', response.scope);
      }
    }

    return response;
  }

  /**
   * Verifica si el token actual ha expirado
   */
  isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;
    
    return new Date() >= new Date(expiresAt);
  }

  /**
   * Refresca el token si está próximo a expirar
   */
  async refreshTokenIfNeeded(): Promise<void> {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return;
    
    const expirationDate = new Date(expiresAt);
    const now = new Date();
    const timeUntilExpiry = expirationDate.getTime() - now.getTime();
    const fiveMinutes = 5 * 60 * 1000; // 5 minutos en millisegundos
    
    // Si el token expira en menos de 5 minutos, necesitamos renovarlo
    if (timeUntilExpiry < fiveMinutes) {
      console.log('🔄 Token próximo a expirar, renovación necesaria');
      // Aquí podrías implementar la lógica de refresh token si la tienes
      // Por ahora, simplemente limpiar el token expirado
      this.clearToken();
    }
  }

  /**
   * Limpia el token almacenado
   */
  clearToken(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('token_scopes');
  }

  /**
   * Obtiene el token actual almacenado
   */
  getCurrentToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Obtiene los scopes del token actual
   */
  getTokenScopes(): string[] {
    const scopes = localStorage.getItem('token_scopes');
    return scopes ? scopes.split(' ') : [];
  }

  /**
   * Login usando OAuth2 con scopes específicos
   */
  async login(email: string, password: string, scopes?: string): Promise<OAuth2TokenResponse> {
    return this.getToken({ 
      username: email, 
      password,
      scope: scopes 
    });
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    this.clearToken();
    
    // Opcionalmente, llamar al endpoint de logout del backend
    try {
      await this.makeRequest('/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.warn('Warning: Error calling logout endpoint:', error);
    }
  }
}

export const oauth2Service = new OAuth2Service();
