// Representación interna (frontend) de una Unidad.
// Usamos id como string (UUID del backend) y camelCase para fechas.
export interface Unit {
  id: string;
  code?: string;
  name: string;
  symbol: string;
  description?: string | null;
  active?: boolean;
  userId?: string; // user_id en backend
  createdAt?: string; // created_at en backend
  updatedAt?: string | null; // updated_at en backend
}

// Respuesta estándar del endpoint GET /units (UnitListResponse backend)
export interface UnitListResponseDTO {
  total: number;
  items: UnitReadDTO[];
}

// Forma exacta que devuelve el backend (UnitRead)
export interface UnitReadDTO {
  id: string;
  name: string;
  symbol: string;
  description?: string | null;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateUnitData {
  name: string;
  symbol: string;
  description?: string;  
  active?: boolean;
}

export interface UpdateUnitData extends Partial<CreateUnitData> {
  id: string;
  code?: string;
}

// Utilidad de transformación DTO -> Unit
export function mapUnit(dto: UnitReadDTO): Unit {
  return {
    id: dto.id,  
    name: dto.name,
    symbol: dto.symbol,   
    description: dto.description,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
