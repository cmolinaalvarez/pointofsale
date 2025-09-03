// Representación interna (frontend) de una Marca.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Brand {
  id: string;
  name: string;
  code?: string;
  description?: string | null;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /brands (BrandListResponse backend)
export interface BrandListResponseDTO {
  total: number;
  items: BrandReadDTO[];
}

// Forma exacta que devuelve el backend (BrandRead)
export interface BrandReadDTO {
  id: string;
  name: string;
  code?: string;
  description?: string | null;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateBrandData {
  code: string;
  name: string;
  description?: string;
  active?: boolean;
}

export interface UpdateBrandData extends Partial<CreateBrandData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Brand
export function mapBrand(dto: BrandReadDTO): Brand {
  return {
    id: dto.id,
    name: dto.name,
    code: dto.code,
    description: dto.description,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
