export interface Concept {
  id: string;
  code: string;
  name: string;
  description?: string;
  concept_type: string;
  debit: string;
  debit_account_id: string;
  debit_account_name?: string; // ✅ Nuevo campo
  credit: string;
  credit_account_id: string;
  credit_account_name?: string; // ✅ Nuevo campo
  active: boolean;
  user_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ConceptReadDTO extends Concept {}
export interface ConceptListResponseDTO {
  total: number;
  items: Concept[];
  concept_type_enum: Record<string, string>;
}

export interface CreateConceptData {
  code: string;
  name: string;
  description?: string;
  concept_type: string;
  debit_account_id: string;
  credit: string;
  credit_account_id: string;
  active?: boolean;
}

export interface UpdateConceptData extends Partial<CreateConceptData> {
  id: string;
}

export function mapConcept(dto: ConceptReadDTO): Concept {
  return {
    id: dto.id,
    name: dto.name,
    code: dto.code,
    description: dto.description,
    concept_type: dto.concept_type,
    debit: dto.debit,
    debit_account_id: dto.debit_account_id,
    debit_account_name: dto.debit_account_name, // ✅ Mapear nuevo campo
    credit: dto.credit,
    credit_account_id: dto.credit_account_id,
    credit_account_name: dto.credit_account_name, // ✅ Mapear nuevo campo
    active: dto.active,
    user_id: dto.user_id,
    created_at: dto.created_at,
    updated_at: dto.updated_at,
  };
}