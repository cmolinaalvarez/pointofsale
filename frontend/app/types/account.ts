// types/account.ts

// Representación interna (frontend) de un Accounto
export interface Account {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  account_type: string;
  active?: boolean;
  userId?: string;
  createdAt?: string;
  updatedAt?: string | null;
}

// ✅ Asegúrate de exportar AccountTypeEnum
export interface AccountTypeEnum {
  [key: string]: string;
}

// Respuesta del endpoint GET /accounts (incluye enum)
export interface AccountListResponseDTO {
  total: number;
  items: AccountReadDTO[];
  account_type_enum: AccountTypeEnum; // ✅ Usar el tipo exportado
}

// Forma exacta que devuelve el backend (AccountRead)
export interface AccountReadDTO {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  account_type: string;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

// Datos para crear un accounto
export interface CreateAccountData {
  code: string;
  name: string;
  description?: string;
  account_type: string;
  active?: boolean;
}

// Datos para actualizar un accounto
export interface UpdateAccountData extends Partial<CreateAccountData> {
  id: string;
}

// Utilidad de transformación DTO -> Account
export function mapAccount(dto: AccountReadDTO): Account {
  return {
    id: dto.id,
    name: dto.name,
    code: dto.code,
    description: dto.description,
    account_type: dto.account_type,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}

// Tipo para opciones del select de accountos
export interface AccountTypeOption {
  value: string;
  label: string;
}