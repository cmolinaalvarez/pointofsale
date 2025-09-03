// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface SubGroup {
  id: string;
  code?: string;
  name: string;
  group_id:string;
  group_name:string;
  description?: string | null;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (SubGroupListResponse backend)
export interface SubGroupListResponseDTO {
  total: number;
  items: SubGroupReadDTO[];
}

// Forma exacta que devuelve el backend (SubGroupRead)
export interface SubGroupReadDTO {
  id: string;
  code?: string;
  name: string;
  group_id:string;
  group_name:string;
  description?: string | null;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateSubGroupData {
  code: string;
  name: string;
  group_id:string;
  description?: string;
  active?: boolean;
}

export interface UpdateSubGroupData extends Partial<CreateSubGroupData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> SubGroup
export function mapSubGroup(dto: SubGroupReadDTO): SubGroup {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    group_id: dto.group_id,
    group_name:dto.group_name,
    description: dto.description,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
