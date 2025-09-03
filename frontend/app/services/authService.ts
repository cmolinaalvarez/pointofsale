class AuthService {
  private apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  
  private getBackendUrl() {
    return this.apiUrl.replace('/api', '');
  }

  async login(email: string, password: string) {
    console.group('🔐 AuthService.login');
    console.log('- Email:', email);
    console.log('- Password length:', password.length);
    
    try {
      const backendUrl = this.getBackendUrl();
      const loginUrl = `${backendUrl}/auth/login`;
      console.log('📡 URL final:', loginUrl);
      
      const loginData = {
        email: email,
        password: password
      };
      
      console.log('📦 JSON payload:', {
        email: loginData.email,
        password: '***'
      });
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      console.log('📥 Response status:', response.status);
      console.log('📥 Response ok:', response.ok);

      const responseText = await response.text();
      console.log('📥 Response text:', responseText.substring(0, 200));

      if (!response.ok) {
        console.error('❌ Response not OK - Status:', response.status);
        
        let errorMessage = 'Error de autenticación';
        let errorDetails = null;
        
        try {
          errorDetails = JSON.parse(responseText);
          console.error('❌ Error details:', errorDetails);
          
          if (errorDetails.detail && Array.isArray(errorDetails.detail)) {
            const validationErrors = errorDetails.detail.map((err: any) => 
              `${err.loc?.join('.')}: ${err.msg}`
            ).join(', ');
            errorMessage = `Error de validación: ${validationErrors}`;
          } else {
            errorMessage = errorDetails.detail || errorDetails.message || 'Credenciales incorrectas';
          }
        } catch (e) {
          console.error('❌ Raw error response:', responseText);
          errorMessage = responseText || 'Error del servidor';
        }
        
        console.groupEnd();
        throw new Error(errorMessage);
      }

      let data;
      try {
        data = JSON.parse(responseText);
        console.log('✅ Response parsed successfully');
        console.log('✅ Access token present:', !!data.access_token);
      } catch (e) {
        console.error('❌ No se pudo parsear respuesta exitosa como JSON');
        console.groupEnd();
        throw new Error('Respuesta inválida del servidor');
      }

      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user || { email }));
        console.log('💾 Token guardado en localStorage');
      }

      console.groupEnd();
      return data;
    } catch (error: any) {
      console.error('💥 Error en login:', error);
      console.groupEnd();
      throw error;
    }
  }

  // Método para obtener token OAuth2 con client credentials (para endpoints protegidos)
  async getOAuth2Token(): Promise<string> {
    const backendUrl = this.getBackendUrl();
    const tokenUrl = `${backendUrl}/auth/token`;
    
    console.log('🔑 Solicitando token OAuth2...');
    
    try {
      const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'client_credentials',
          // Estos valores deberían venir de variables de entorno o configuración
          client_id: process.env.NEXT_PUBLIC_CLIENT_ID || 'your_client_id',
          client_secret: process.env.NEXT_PUBLIC_CLIENT_SECRET || 'your_client_secret',
        }),
      });

      if (!response.ok) {
        throw new Error(`Error obteniendo token OAuth2: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Token OAuth2 obtenido');
      
      return data.access_token;
    } catch (error) {
      console.error('❌ Error obteniendo token OAuth2:', error);
      throw error;
    }
  }

  async register(userData: any) {
    try {
      const backendUrl = this.getBackendUrl();
      const registerUrl = `${backendUrl}/auth/register`;
      
      const response = await fetch(registerUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = 'Error en el registro';
        
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorData.message || 'Error en el registro';
        } catch (e) {
          errorMessage = responseText || 'Error del servidor';
        }
        
        throw new Error(errorMessage);
      }

      return JSON.parse(responseText);
    } catch (error: any) {
      throw error;
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getUser(): any {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }
}

export const authService = new AuthService();