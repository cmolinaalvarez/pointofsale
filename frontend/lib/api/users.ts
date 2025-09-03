export async function createUser(data: any, token: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Error');
  return await res.json();
}