// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Division {
  id: string;
  code?: string;
  name: string;
  country_id:string;
  country_name:string;
  description?: string | null;
  country_code:string;  
  iso_3166_2:string;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (DivisionListResponse backend)
export interface DivisionListResponseDTO {
  total: number;
  items: DivisionReadDTO[];
}

// Forma exacta que devuelve el backend (DivisionRead)
export interface DivisionReadDTO {
  id: string;
  code?: string;
  name: string;
  country_id:string;
  country_name:string;
  description?: string | null;
  country_code:string;
  iso_3166_2:string;  
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateDivisionData {
  code: string;
  name: string;
  description?: string;
  country_code:string;
  country_id:string;
  iso_3166_2:string;
  active?: boolean;
}

export interface UpdateDivisionData extends Partial<CreateDivisionData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Division
export function mapDivision(dto: DivisionReadDTO): Division {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    country_id: dto.country_id,
    country_name:dto.country_name,
    description: dto.description,
    country_code:dto.country_code,
    iso_3166_2:dto.iso_3166_2,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
