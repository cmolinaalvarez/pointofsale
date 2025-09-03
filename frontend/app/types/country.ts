// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Country {
  id: string;
  code?: string;
  name: string;
  country_code:string;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /countries (CountryListResponse backend)
export interface CountryListResponseDTO {
  total: number;
  items: CountryReadDTO[];
}

// Forma exacta que devuelve el backend (CountryRead)
export interface CountryReadDTO {
  id: string;
  name: string;
  code?: string;
  country_code:string,
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateCountryData {
  code: string;
  name: string;
  country_code:string,
  active?: boolean;
}

export interface UpdateCountryData extends Partial<CreateCountryData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Country
export function mapCountry(dto: CountryReadDTO): Country {
  return {
    id: dto.id,
    name: dto.name,
    code: dto.code,
    country_code:dto.country_code,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}