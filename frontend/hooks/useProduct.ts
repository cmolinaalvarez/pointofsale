import { useState, useEffect, useCallback } from "react";
import { Product, CreateProductData, UpdateProductData } from "@/app/types/product";
import { productService } from "@/app/services/productService";

export function useProduct(token: string | null) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10); // por defecto 10

  const handleError = (err: unknown): string => {
    console.error("Error completo en useProduct:", err);

    if (err instanceof Error) {
      console.error("Error message:", err.message);
      console.error("Error stack:", err.stack);

      if (err.message.includes("401")) {
        return "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.";
      }
      if (err.message.includes("403")) {
        return "No tienes permisos para acceder a esta información.";
      }
      if (err.message.includes("404")) {
        return "El recurso solicitado no fue encontrado.";
      }
      if (err.message.includes("500")) {
        return "Error interno del servidor. Intenta nuevamente más tarde.";
      }
      if (err.message.includes("timeout") || err.message.includes("Network")) {
        return "Tiempo de espera agotado. Verifica tu conexión a internet.";
      }
      return err.message;
    }
    return "Error inesperado al procesar la solicitud";
  };

  const fetchProducts = useCallback(async () => {
    console.log("=== INICIANDO FETCH PRODUCTS ===");
    console.log("Token disponible:", !!token);
    console.log("Token value:", token ? token.substring(0, 20) + "..." : "null");

    if (!token || token.trim() === "") {
      console.log("❌ Token inválido, saltando fetch");
      setError("Token de autenticación no válido");
      return;
    }

    setLoading(true);
    setError(null);
    console.log("🔄 Loading iniciado");

    try {
      console.log("📡 Llamando a productService.getProducts...");
  const skip = (page - 1) * pageSize;
  const response = await productService.getProducts(token, { skip, limit: pageSize });
      console.log("✅ Respuesta recibida:", response);
      console.log("Tipo de respuesta:", typeof response);
      console.log("Es array?:", Array.isArray(response));

      // Inspeccionar la estructura completa
      if (response) {
        console.log("Claves de la respuesta:", Object.keys(response));

        // Intentar diferentes estructuras
        let productsData: any[] = [];

        if (Array.isArray(response)) {
          console.log("📦 Respuesta es array directo");
          productsData = response;
        } else if (response.data && Array.isArray(response.data)) {
          console.log("📦 Respuesta tiene data array");
          productsData = response.data;
        } else if (response.items && Array.isArray(response.items)) {
          // soporte estructura { total, items }
          productsData = response.items;
          if (typeof response.total === 'number') setTotal(response.total);
        } else if (response.products && Array.isArray(response.products)) {
          console.log("📦 Respuesta tiene products array");
          productsData = response.products;
        } else if (response.result && Array.isArray(response.result)) {
          console.log("📦 Respuesta tiene result array");
          productsData = response.result;
        } else {
          console.log("❓ Estructura desconocida, intentando convertir a array");
          productsData = [];
        }

        console.log("📊 Productos extraídos:", productsData);
        console.log("📊 Cantidad de productos:", productsData.length);

        if (productsData.length > 0) {
          console.log("📊 Primer producto:", productsData[0]);
        }

        setProducts(productsData);
        if (!response?.total) {
          setTotal(productsData.length + (skip || 0)); // estimación si no se provee
        }
      } else {
        console.log("❌ Respuesta vacía o nula");
        setProducts([]);
        setTotal(0);
      }
    } catch (err) {
      console.error("💥 Error en fetchProducts:", err);
      const errorMessage = handleError(err);
      setError(errorMessage);
      setProducts([]);
      setTotal(0);
    } finally {
      setLoading(false);
      console.log("🏁 Loading finalizado");
    }
  }, [token, page, pageSize]);

  const createProduct = async (
    productData: CreateProductData
  ): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }

    try {
      setError(null);
      const newProduct = await productService.createProduct(productData, token!);
      setProducts((prev) => [...prev, newProduct]);
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const updateProduct = async (
    productData: UpdateProductData
  ): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }

    try {
      setError(null);
  const updatedProduct = await productService.updateProduct(String(productData.id), productData, token!);
      setProducts((prev) =>
        prev.map((p) => (p.id === updatedProduct.id ? updatedProduct : p))
      );
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  const deleteProduct = async (id: number): Promise<boolean> => {
    if (!token || token.trim() === "") {
      setError("Token de autenticación no válido");
      return false;
    }

    try {
      setError(null);
  await productService.deleteProduct(String(id), token!);
      setProducts((prev) => prev.filter((p) => p.id !== id));
      return true;
    } catch (err) {
      setError(handleError(err));
      return false;
    }
  };

  useEffect(() => {
    console.log("🔄 useEffect ejecutándose, token cambió:", !!token, "page", page, "pageSize", pageSize);
    fetchProducts();
  }, [fetchProducts]);

  const totalPages = Math.max(1, Math.ceil((total || 1) / pageSize));
  const goToPage = (p: number) => setPage(Math.min(Math.max(1, p), totalPages));

  return {
    products,
    loading,
    error,
    refetch: fetchProducts,
    total,
    page,
    pageSize,
    totalPages,
    setPage: goToPage,
    setPageSize,
    createProduct,
    updateProduct,
    deleteProduct,
    clearError: () => setError(null),
  };
}
