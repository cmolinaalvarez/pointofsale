export interface Brand {
  id?: string;
  nombre: string;
  descripcion?: string;
  activo: boolean;
  creadoEn?: string;
  actualizadoEn?: string;
}

const BASE_URL = '/api/brands'; // Ajustar según tu backend

async function http<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Error HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const brandService = {
  list: () => http<Brand[]>(BASE_URL),
  get: (id: string) => http<Brand>(`${BASE_URL}/${id}`),
  create: (data: Omit<Brand, 'id'>) => http<Brand>(BASE_URL, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Brand>) =>
    http<Brand>(`${BASE_URL}/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  remove: (id: string) => http<void>(`${BASE_URL}/${id}`, { method: 'DELETE' })
};
