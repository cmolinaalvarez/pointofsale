export interface Category {
  id: string;
  code: string;
  name: string;
  description?: string;
  active: boolean;
  createdAt?: string | Date;
  updatedAt?: string | Date;
  userId?: string;
}

export interface CreateCategoryData {
  code: string;
  name: string;
  description?: string;
  active?: boolean;
}

export interface UpdateCategoryData extends CreateCategoryData {
  id: string;
}

export interface CategoryListResponseDTO {
  total: number;
  items: Category[];
}

// Utilidad para mapear datos del backend al modelo Category
export function mapCategory(data: any): Category {
  return {
    id: data.id,
    code: data.code,
    name: data.name,
    description: data.description,
    active: !!data.active,
    createdAt: data.createdAt,
    updatedAt: data.updatedAt,
    userId: data.userId,
  };
}
