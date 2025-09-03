"use client"

import { useAuthContext } from "@/context/AuthContext"
import { useRouter } from "next/navigation"
import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  ChevronDown,
  ChevronRight,
  Home,
  Users,
  Package,
  ShoppingCart,
  Settings,
  Building,
  Truck,
  Archive,
  Menu,
  X,
  ChevronLeft,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface MenuItem {
  title: string
  icon: React.ReactNode
  href?: string
  children?: MenuItem[]
  visible?: boolean
}

const menuItems: MenuItem[] = [
  {
    title: "Dashboard",
    icon: <Home className="w-5 h-5" />,
    href: "/",
  },
  {
    title: "Usuarios",
    icon: <Users className="w-5 h-5" />,
    visible: false,
    children: [
      { title: "Lista", icon: null, href: "/users" },
      { title: "Crear", icon: null, href: "/users/create" },
    ],
  },
  {
    title: "Productos",
    icon: <Package className="w-5 h-5" />,
    children: [
      { title: "Marcas", icon: null, href: "/brands" },
      { title: "Categorías", icon: null, href: "/categories" },
      { title: "Subcategorías", icon: null, href: "/subcategories" },
      { title: "Grupos", icon: null, href: "/groups" },
      { title: "Subgrupos", icon: null, href: "/subgroups" },
      { title: "Productos", icon: null, href: "/products" },
      { title: "Unidades", icon: null, href: "/units" },
    ],
  },
  {
    title: "Ventas",
    icon: <ShoppingCart className="w-5 h-5" />,
    children: [
      { title: "Lista", icon: null, href: "/sales" },
      { title: "Crear", icon: null, href: "/sales/create" },
      { title: "Órdenes", icon: null, href: "/orders" },
    ],
  },
  {
    title: "Compras",
    icon: <Truck className="w-5 h-5" />,
    children: [
      { title: "Lista", icon: null, href: "/purchases" },
      { title: "Crear", icon: null, href: "/purchases/create" },
      { title: "Entradas", icon: null, href: "/entries" },
    ],
  },
  {
    title: "Inventario",
    icon: <Archive className="w-5 h-5" />,
    children: [
      { title: "Bodegas", icon: null, href: "/warehouses" },
      { title: "Salidas", icon: null, href: "/issues" },
      { title: "Transferencias", icon: null, href: "/transfers" },
    ],
  },
  {
    title: "Terceros",
    icon: <Building className="w-5 h-5" />,
    children: [
      { title: "Lista", icon: null, href: "/third-parties" },
      { title: "Crear", icon: null, href: "/third-parties/create" },
    ],
  },
  {
    title: "Configuración",
    icon: <Settings className="w-5 h-5" />,
    children: [
      { title: "Cuentas", icon: null, href: "/accounts" },
      { title: "Conceptos", icon: null, href: "/concepts" },
      { title: "Documentos", icon: null, href: "/documents" },
      { title: "Países", icon: null, href: "/countries" },
      { title: "Divisiones", icon: null, href: "/divisions" },
      { title: "Municipios", icon: null, href: "/municipalities" },
      { title: "Términos de Pago", icon: null, href: "/paymentterms" },
      { title: "Configuración General", icon: null, href: "/settings" },
    ],
  },
]

export function Sidebar() {
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()
  const { isAuthenticated } = useAuthContext();
  const router = useRouter();

  // Detectar tamaño de pantalla
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024; // lg breakpoint
      setIsMobile(mobile);
      
      // En móviles, el sidebar siempre está cerrado por defecto
      if (mobile) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };
    
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleExpanded = (title: string) => {
    setExpandedItems((prev) => (prev.includes(title) ? prev.filter((item) => item !== title) : [...prev, title]))
  }

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
  }

  const renderMenuItem = (item: MenuItem, level = 0) => {
    const isExpanded = expandedItems.includes(item.title);
    const isActive = item.href === pathname;
    const hasChildren = item.children && item.children.length > 0;

    if (item.visible === false) return null;

    const disabledClass = !isAuthenticated ? "opacity-50 pointer-events-none select-none" : "";

    return (
      <div key={item.title}>
        {hasChildren ? (
          <button
            onClick={() => isAuthenticated && toggleExpanded(item.title)}
            className={cn(
              "w-full flex items-center justify-between px-4 py-3 text-left text-base font-medium rounded-xl transition-colors",
              level === 0 ? "text-gray-700 hover:bg-blue-50 hover:text-blue-700" : "text-gray-600 hover:bg-gray-100",
              level > 0 && "ml-4",
              disabledClass,
              isCollapsed && "justify-center px-3"
            )}
            disabled={!isAuthenticated}
          >
            <div className="flex items-center space-x-3">
              {item.icon}
              {(!isCollapsed && isSidebarOpen) && <span className="truncate text-base">{item.title}</span>}
            </div>
            {(!isCollapsed && isSidebarOpen) && (isExpanded ? (
              <ChevronDown className="w-4 h-4 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-4 h-4 flex-shrink-0" />
            ))}
          </button>
        ) : (
          <Link
            href={item.href || "#"}
            onClick={() => isMobile && setIsSidebarOpen(false)}
            className={cn(
              "flex items-center space-x-3 px-4 py-3 text-base font-medium rounded-xl transition-colors",
              level === 0 ? "text-gray-700 hover:bg-blue-50 hover:text-blue-700" : "text-gray-600 hover:bg-gray-100",
              level > 0 && "ml-4",
              isActive && "bg-blue-100 text-blue-700 shadow-sm",
              disabledClass,
              isCollapsed && "justify-center px-3"
            )}
            tabIndex={0}
            aria-disabled={!isAuthenticated}
          >
            {item.icon && item.icon}
            {(!isCollapsed && isSidebarOpen) && <span className="truncate text-base">{item.title}</span>}
          </Link>
        )}
        {hasChildren && isExpanded && (!isCollapsed && isSidebarOpen) && (
          <div className="mt-1 space-y-1">{item.children?.map((child) => renderMenuItem(child, level + 1))}</div>
        )}
      </div>
    );
  }

  // En móviles, mostrar botón de hamburguesa y sidebar overlay
  if (isMobile) {
    return (
      <>
        {/* Botón hamburguesa flotante */}
        {isAuthenticated && !isSidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="fixed top-4 left-4 z-50 p-3 bg-white rounded-full shadow-lg border hover:bg-gray-100"
            aria-label="Abrir menú"
          >
            <Menu className="w-7 h-7 text-gray-700" />
          </button>
        )}

        {/* Overlay de fondo cuando el menú está abierto */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-blue-100 bg-opacity-80 z-40 lg:hidden"
            //className="fixed inset-0 bg-[url('/assets/images/glass-of-orange-juice.png')] bg-cover bg-center bg-blur flex items-center justify-center"
            onClick={toggleSidebar}            
          />        
        )} 

         
        
        {/* Sidebar para móviles */}
        <aside
          className={cn(
            "bg-white shadow-2xl transition-all duration-300 ease-in-out z-50 fixed inset-y-0 left-0 w-64 flex flex-col lg:hidden",
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          {/* Header del sidebar con botón de cerrar */}
          <div className="p-6 border-b flex flex-col items-center bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="w-full flex justify-between items-start mb-4">
              <div className="flex flex-col items-center flex-1">
                <img src="/icon.png" alt="Logo" className="w-24 h-16 mb-2 object-contain" />
                <p className="text-sm text-gray-600 font-medium">Carlos Molina</p>
              </div>
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-full bg-white shadow-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                aria-label="Cerrar menú"
              >
                <X className="w-6 h-6 text-gray-600" />
              </button>
            </div>
          </div>
          
          {/* Navegación */}
          <nav className="flex-1 p-6 space-y-3 overflow-y-auto bg-white">
            {menuItems.map((item) => renderMenuItem(item))}
          </nav>
          
          {/* Footer con copyright */}
          
        </aside>
      </>
    );
  }

  // Sidebar para escritorio
  return (
    <>
      {/* Botón para mostrar/ocultar sidebar en escritorio */}
      {!isSidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed top-4 left-4 z-30 p-2 bg-white rounded shadow border hover:bg-gray-100 hidden lg:block"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5 text-gray-700" />
        </button>
      )}
      
      <aside
        className={cn(
          "bg-white shadow-lg h-full z-40 flex flex-col transition-all duration-300 ease-in-out lg:relative",
          isSidebarOpen ? "w-64" : "w-0 overflow-hidden",
          isCollapsed && "w-20"
        )}
        style={{ height: '100vh' }}
      >
        {/* Header con botón de cerrar y colapsar */}
        <div className="p-4 border-b flex flex-col items-center relative">
          <img 
            src="/icon.png" 
            alt="Logo" 
            className={cn(
              "object-contain transition-opacity duration-300 mb-2",
              isCollapsed ? "w-10 h-8 opacity-70" : "w-24 h-16"
            )} 
          />
          {!isCollapsed && <p className="text-xs text-gray-600">Carlos Molina</p>}
          
          {/* Botón para colapsar/expandir (solo visible cuando sidebar está abierto) */}
          {isSidebarOpen && (
            <button
              onClick={toggleCollapse}
              // className="absolute -right-3 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-1 shadow-md border border-gray-200 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              className="absolute -right-3 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-1"
              aria-label={isCollapsed ? "Expandir sidebar" : "Colapsar sidebar"}
            >
              <ChevronLeft className={cn(
                "w-4 h-4 text-gray-600 transition-transform duration-300",
                isCollapsed && "rotate-180"
              )} />
            </button>
          )}
          
          {/* Botón para cerrar sidebar */}
          <button
            onClick={toggleSidebar}
            className="absolute -right-3 top-6 transform translate-y-full mt-2 bg-white rounded-full p-1 shadow-md border border-gray-200 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors lg:hidden"
            aria-label="Cerrar menú"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>
        
        {/* Navegación */}
        <nav className={cn(
          "flex-1 p-4 space-y-2 overflow-y-auto",
          isCollapsed && "flex items-center flex-col"
        )}>
          {menuItems.map((item) => renderMenuItem(item))}
        </nav>
        
        {/* Footer con copyright */}
        <div className={cn(
          "p-4 border-t bg-gray-50 text-center transition-opacity duration-300",
          isCollapsed ? "opacity-0 h-0 overflow-hidden" : "opacity-100"
        )}>
          <p className="text-xs text-gray-500 mb-1">Sistema POS v1.0</p>
          <p className="text-xs text-gray-400">© 2025 Todos los derechos reservados</p>
          <p className="text-xs text-gray-400">Desarrollado por Carlos Molina</p>
        </div>
      </aside>
    </>
  );
}