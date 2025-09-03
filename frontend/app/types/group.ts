// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Group {
  id: string;
  code?: string;
  name: string;
  subcategory_id:string;
  subcategory_name:string;
  description?: string | null;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (GroupListResponse backend)
export interface GroupListResponseDTO {
  total: number;
  items: GroupReadDTO[];
}

// Forma exacta que devuelve el backend (GroupRead)
export interface GroupReadDTO {
  id: string;
  code?: string;
  name: string;
  subcategory_id:string;
  subcategory_name:string;
  description?: string | null;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateGroupData {
  code: string;
  name: string;
  category_id:string;
  description?: string;
  active?: boolean;
}

export interface UpdateGroupData extends Partial<CreateGroupData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Group
export function mapGroup(dto: GroupReadDTO): Group {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    subcategory_id: dto.subcategory_id,
    subcategory_name:dto.subcategory_name,
    description: dto.description,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
