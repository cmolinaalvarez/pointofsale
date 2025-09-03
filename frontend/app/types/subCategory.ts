// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface SubCategory {
  id: string;
  code?: string;
  name: string;
  category_id:string;
  category_name:string;
  description?: string | null;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (SubCategoryListResponse backend)
export interface SubCategoryListResponseDTO {
  total: number;
  items: SubCategoryReadDTO[];
}

// Forma exacta que devuelve el backend (SubCategoryRead)
export interface SubCategoryReadDTO {
  id: string;
  code?: string;
  name: string;
  category_id:string;
  category_name:string;
  description?: string | null;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateSubCategoryData {
  code: string;
  name: string;
  category_id:string;
  description?: string;
  active?: boolean;
}

export interface UpdateSubCategoryData extends Partial<CreateSubCategoryData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> SubCategory
export function mapSubCategory(dto: SubCategoryReadDTO): SubCategory {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    category_id: dto.category_id,
    category_name:dto.category_name,
    description: dto.description,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
