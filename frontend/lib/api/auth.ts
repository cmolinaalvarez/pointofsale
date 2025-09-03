// lib/api/auth.ts
export async function loginUser(email: string, password: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Credenciales incorrectas");
  return await res.json(); // Debe devolver el token
}

export async function logoutUser() {
  const token = localStorage.getItem("token");
  
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });
    
    // Independientemente de la respuesta del servidor, limpiamos el token local
    localStorage.removeItem("token");
    
    if (!res.ok) {
      console.warn("Error al cerrar sesión en el servidor, pero token local eliminado");
    }
    
    return { success: true, message: "Sesión cerrada correctamente" };
  } catch (error) {
    // Aún si hay error de red, eliminamos el token local
    localStorage.removeItem("token");
    console.warn("Error de red al cerrar sesión, pero token local eliminado");
    return { success: true, message: "Sesión cerrada localmente" };
  }
}
