"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { logoutUser } from "@/lib/api/auth";

interface AuthContextType {
  isAuthenticated: boolean;
  setIsAuthenticated: (value: boolean) => void;
  isLoading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const logout = async () => {
    try {
      await logoutUser();
      setIsAuthenticated(false);
    } catch (error) {
      console.error("Error al cerrar sesión:", error);
      // Aún con error, desautenticamos localmente
      setIsAuthenticated(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    
    const checkToken = () => {
      if (!mounted) return;
      
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      setIsAuthenticated(!!token);
      
      // Siempre establecer loading a false después de la primera verificación
      if (isLoading) {
        setIsLoading(false);
      }
    };

    // Verificación inicial
    checkToken();
    
    // Verificar cada 1 segundo
    const interval = setInterval(checkToken, 1000);
    
    // Escuchar cambios en localStorage
    window.addEventListener("storage", checkToken);
    
    return () => {
      mounted = false;
      clearInterval(interval);
      window.removeEventListener("storage", checkToken);
    };
  }, [isLoading]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated, isLoading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuthContext debe usarse dentro de AuthProvider");
  return context;
}
