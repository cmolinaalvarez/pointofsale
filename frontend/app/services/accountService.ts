import { AccountListResponseDTO, CreateAccountData, UpdateAccountData, AccountReadDTO } from '@/app/types/account';
import { authService } from './authService';

class AccountService {
  private apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  private getBackendUrl() {
    return this.apiUrl.replace('/api', '');
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const backendUrl = this.getBackendUrl();
    const url = `${backendUrl}${endpoint}`;

    console.group('🚀 AccountService Request');
    console.log('📡 URL:', url);
    console.log('🔧 Method:', options.method || 'GET');
    console.log('🔑 Headers:', options.headers);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
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
          throw new Error('Token de autenticación inválido o expirado');
        }
        if (response.status === 403) {
          throw new Error('No tienes permisos para acceder a este recurso');
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

  async getAccounts(tokenOrParams?: string | {
    skip?: number;
    limit?: number; 
    search?: string;
    active?: boolean;
  }, params?: {
    skip?: number;
    limit?: number; 
    search?: string;
    active?: boolean;
  }): Promise<AccountListResponseDTO> {
    console.log('🎯 getAccounts called');

    let authToken: string;
    let queryParams: any = {};

    if (typeof tokenOrParams === 'string') {
      authToken = tokenOrParams;
      queryParams = params || {};
    } else {
      authToken = authService.getToken() || '';
      queryParams = tokenOrParams || {};
    }

    if (!authToken) {
      throw new Error('No hay token de autenticación. Por favor, inicia sesión.');
    }

    console.log('🔑 Using token:', authToken?.substring(0, 20) + '...');

    const searchParams = new URLSearchParams();
    if (queryParams.skip !== undefined) searchParams.append('skip', queryParams.skip.toString());
    if (queryParams.limit !== undefined) searchParams.append('limit', queryParams.limit.toString());
    if (queryParams.search) searchParams.append('search', queryParams.search);
    if (queryParams.active !== undefined) searchParams.append('active', queryParams.active.toString());

    const queryString = searchParams.toString();
    const endpoint = `/accounts/${queryString ? `?${queryString}` : ''}`;

  return await this.makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });
  }

  async getAccount(id: string, token: string): Promise<AccountReadDTO> {
    return await this.makeRequest(`/accounts/${id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async createAccount(accountData: CreateAccountData, token: string): Promise<AccountReadDTO> {
    return await this.makeRequest('/accounts/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(accountData),
    });
  }

  async updateAccount(id: string, accountData: UpdateAccountData, token: string): Promise<AccountReadDTO> {
    return await this.makeRequest(`/accounts/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(accountData),
    });
  }

  async deleteAccount(id: string, token: string): Promise<any> {
    return await this.makeRequest(`/accounts/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }
}

export const accountService = new AccountService();
