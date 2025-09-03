// types/document.ts

// Representación interna (frontend) de un Documento
export interface Document {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  prefix: string;
  document_type: string;
  active?: boolean;
  userId?: string;
  createdAt?: string;
  updatedAt?: string | null;
}

// ✅ Asegúrate de exportar DocumentTypeEnum
export interface DocumentTypeEnum {
  [key: string]: string;
}

// Respuesta del endpoint GET /documents (incluye enum)
export interface DocumentListResponseDTO {
  total: number;
  items: DocumentReadDTO[];
  document_type_enum: DocumentTypeEnum; // ✅ Usar el tipo exportado
}

// Forma exacta que devuelve el backend (DocumentRead)
export interface DocumentReadDTO {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  prefix: string;
  document_type: string;
  active?: boolean;
  user_id: string;
  created_at: string;
  updated_at?: string | null;
}

// Datos para crear un documento
export interface CreateDocumentData {
  code: string;
  name: string;
  description?: string;
  prefix: string;
  document_type: string;
  active?: boolean;
}

// Datos para actualizar un documento
export interface UpdateDocumentData extends Partial<CreateDocumentData> {
  id: string;
}

// Utilidad de transformación DTO -> Document
export function mapDocument(dto: DocumentReadDTO): Document {
  return {
    id: dto.id,
    name: dto.name,
    code: dto.code,
    description: dto.description,
    prefix: dto.prefix,
    document_type: dto.document_type,
    active: dto.active,
    userId: dto.user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}

// Tipo para opciones del select de documentos
export interface DocumentTypeOption {
  value: string;
  label: string;
}