export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock?: number;
  category?: string;
  image?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface ProductResponse {
  data: Product[];
  total?: number;
  page?: number;
  limit?: number;
}

export interface CreateProductData {
  name: string;
  description?: string;
  price: number;
  stock?: number;
  category?: string;
  image?: string;
}

export interface UpdateProductData extends Partial<CreateProductData> {
  id: number;
}
