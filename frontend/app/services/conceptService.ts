import { ConceptListResponseDTO, CreateConceptData, UpdateConceptData, ConceptReadDTO } from '@/app/types/concept';
import { authService } from './authService';

class ConceptService {
  private apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  private getBackendUrl() {
    return this.apiUrl.replace('/api', '');
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const backendUrl = this.getBackendUrl();
    const url = `${backendUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        if (response.status === 401) {
          throw new Error('Token de autenticación inválido o expirado');
        }
        if (response.status === 403) {
          throw new Error('No tienes permisos para acceder a este recurso');
        }
        throw new Error(`HTTP ${response.status}: ${errorText || 'Error del servidor'}`);
      }

      return response.json();
    } catch (error) {
      throw error;
    }
  }

  async getConcepts(token: string, params: {
    skip?: number;
    limit?: number; 
    search?: string;
    active?: boolean;
  }): Promise<ConceptListResponseDTO> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.active !== undefined) searchParams.append('active', params.active.toString());

    const queryString = searchParams.toString();
    const endpoint = `/concepts/${queryString ? `?${queryString}` : ''}`;

    return await this.makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

async getConcept(id: string, token: string): Promise<ConceptReadDTO> {
    return await this.makeRequest(`/concepts/${id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async createConcept(conceptData: CreateConceptData, token: string): Promise<ConceptReadDTO> {
    return await this.makeRequest('/concepts/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(conceptData),
    });
  }

  async updateConcept(id: string, conceptData: UpdateConceptData, token: string): Promise<ConceptReadDTO> {
    return await this.makeRequest(`/concepts/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(conceptData),
    });
  }

  async deleteConcept(id: string, token: string): Promise<any> {
    return await this.makeRequest(`/concepts/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }
}

export const conceptService = new ConceptService();
