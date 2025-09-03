// hooks/useAuth.ts
export function useAuth() {
  if (typeof window === "undefined") return { token: "" };
  const token = localStorage.getItem("token") || "";
  return { token };
}
