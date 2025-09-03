export interface PaymentTerm {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  netDays: number;
  discountPercent: number;
  discountDays: number;
  basis: string;
  active?: boolean;
  userId?: string;
  createdAt?: string;
  updatedAt?: string | null;
}

export interface PaymentTermListResponseDTO {
  total: number;
  items: PaymentTermReadDTO[];
}

export interface PaymentTermReadDTO {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  net_days: number;
  discount_percent: number;
  discount_days: number;
  basis: string;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreatePaymentTermData {
  code: string;
  name: string;
  description?: string;
  netDays: number;
  discountPercent: number;
  discountDays: number;
  basis: string;
  active?: boolean;
}

export interface UpdatePaymentTermData extends Partial<CreatePaymentTermData> {
  id: string;
}

export function mapPaymentTerm(dto: PaymentTermReadDTO): PaymentTerm {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    description: dto.description,
    netDays: dto.net_days,
    discountPercent: dto.discount_percent,
    discountDays: dto.discount_days,
    basis: dto.basis,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}