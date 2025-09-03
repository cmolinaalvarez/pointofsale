// lib/api/products.ts
export async function fetchProducts(token: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/products/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error('Error al obtener productos');
  return await res.json();
}
