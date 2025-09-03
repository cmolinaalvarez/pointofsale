// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Municipality {
  id: string;
  code?: string;
  name: string;
  division_id:string;
  division_name:string;
  division_code:string;  
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (MunicipalityListResponse backend)
export interface MunicipalityListResponseDTO {
  total: number;
  items: MunicipalityReadDTO[];
}

// Forma exacta que devuelve el backend (MunicipalityRead)
export interface MunicipalityReadDTO {
  id: string;
  code?: string;
  name: string;
  division_id:string;
  division_name:string;
  description?: string | null;
  divisio_code:string;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateMunicipalityData {
  code: string;
  name: string;
  description?: string;
  division_code:string;
  division_id:string;
  active?: boolean;
}

export interface UpdateMunicipalityData extends Partial<CreateMunicipalityData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Municipality
export function mapMunicipality(dto: MunicipalityReadDTO): Municipality {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    division_id: dto.division_id,
    division_name:dto.division_name,
    division_code:dto.division_code,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
