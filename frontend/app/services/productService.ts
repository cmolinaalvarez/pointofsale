import { Product, ProductResponse, CreateProductData, UpdateProductData } from '@/app/types/product';
import { authService } from './authService';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ProductService {
  private apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  // Método para obtener la URL base sin /api (proxy temporal)
  private getBackendUrl() {
    return this.apiUrl.replace('/api', '');
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    // Usar URL temporal sin /api hasta configurar backend
    const backendUrl = this.getBackendUrl();
    const url = `${backendUrl}${endpoint}`;
    
    console.group('🚀 ProductService Request');
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

  async getProducts(tokenOrParams?: string | {
    skip?: number;
    limit?: number; 
    search?: string;
    active?: boolean;
  }, params?: {
    skip?: number;
    limit?: number; 
    search?: string;
    active?: boolean;
  }): Promise<any> {
    console.log('🎯 getProducts called');
    
    // Determinar si el primer parámetro es token o params
    let authToken: string;
    let queryParams: any = {};
    
    if (typeof tokenOrParams === 'string') {
      // Caso: getProducts(token, params)
      authToken = tokenOrParams;
      queryParams = params || {};
    } else {
      // Caso: getProducts(params)
      authToken = authService.getToken() || '';
      queryParams = tokenOrParams || {};
    }
    
    if (!authToken) {
      throw new Error('No hay token de autenticación. Por favor, inicia sesión.');
    }
    
    console.log('🔑 Using token:', authToken?.substring(0, 20) + '...');
    
    // Construir query string
    const searchParams = new URLSearchParams();
    if (queryParams.skip !== undefined) searchParams.append('skip', queryParams.skip.toString());
    if (queryParams.limit !== undefined) searchParams.append('limit', queryParams.limit.toString());
    if (queryParams.search) searchParams.append('search', queryParams.search);
    if (queryParams.active !== undefined) searchParams.append('active', queryParams.active.toString());
    
    const queryString = searchParams.toString();
    const endpoint = `/products/${queryString ? `?${queryString}` : ''}`;
    
    return await this.makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });
  }

  async getProduct(id: string, token: string): Promise<any> {
    return await this.makeRequest(`/products/${id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async createProduct(productData: any, token: string): Promise<any> {
    return await this.makeRequest('/products/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(productData),
    });
  }

  async updateProduct(id: string, productData: any, token: string): Promise<any> {
    return await this.makeRequest(`/products/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(productData),
    });
  }

  async deleteProduct(id: string, token: string): Promise<any> {
    return await this.makeRequest(`/products/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }
}

export const productService = new ProductService();