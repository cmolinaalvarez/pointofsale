"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X, Printer, Menu } from "lucide-react"

export interface CartItem {
  id: string
  name: string
  price: number
  quantity: number
  image: string
  subtotal: number
  discount: number
  tax: number
  total: number
}

export interface Product {
  id: string
  name: string
  price: number
  category: string
  image: string
  stock: number
  displayNumber: number
}

export interface POSConfig {
  taxRate?: number
  currency?: string
  companyName?: string
  defaultClient?: string
}

interface POSInterfaceProps {
  products?: Product[]
  config?: POSConfig
  onTransaction?: (cart: CartItem[], totals: any) => void
  onPrint?: (cart: CartItem[], totals: any) => void
}

export const defaultProducts: Product[] = [
  { id: "1", name: "CRISTAL", price: 2500, category: "BEBIDAS", image: "/coffee-cup.png", stock: 25, displayNumber: 9 },
  {
    id: "2",
    name: "COCA-COLA",
    price: 3000,
    category: "BEBIDAS",
    image: "/classic-sandwich.png",
    stock: 12,
    displayNumber: 10,
  },
  {
    id: "3",
    name: "AVENA",
    price: 2800,
    category: "BEBIDAS",
    image: "/golden-croissant.png",
    stock: 18,
    displayNumber: 11,
  },
  {
    id: "4",
    name: "ALPINA",
    price: 3200,
    category: "BEBIDAS",
    image: "/elegant-tea-cup.png",
    stock: 30,
    displayNumber: 12,
  },
  { id: "5", name: "PEPSI", price: 3000, category: "BEBIDAS", image: "/fresh-salad.png", stock: 8, displayNumber: 13 },
  {
    id: "6",
    name: "MALTEADA",
    price: 4500,
    category: "BEBIDAS",
    image: "/glass-of-orange-juice.png",
    stock: 15,
    displayNumber: 14,
  },
  {
    id: "7",
    name: "MANZANA",
    price: 2800,
    category: "BEBIDAS",
    image: "/coffee-cup.png",
    stock: 20,
    displayNumber: 15,
  },
  {
    id: "8",
    name: "FRESCOLA",
    price: 2500,
    category: "BEBIDAS",
    image: "/classic-sandwich.png",
    stock: 22,
    displayNumber: 16,
  },
  {
    id: "9",
    name: "HAMBURGUESA",
    price: 8500,
    category: "COMIDAS",
    image: "/golden-croissant.png",
    stock: 10,
    displayNumber: 1,
  },
  {
    id: "10",
    name: "PIZZA",
    price: 12000,
    category: "COMIDAS",
    image: "/elegant-tea-cup.png",
    stock: 5,
    displayNumber: 2,
  },
  {
    id: "11",
    name: "SANDWICH",
    price: 6500,
    category: "COMIDAS",
    image: "/fresh-salad.png",
    stock: 15,
    displayNumber: 3,
  },
  {
    id: "12",
    name: "ENSALADA",
    price: 7500,
    category: "COMIDAS",
    image: "/glass-of-orange-juice.png",
    stock: 12,
    displayNumber: 4,
  },
]

export function POSInterface({ products = defaultProducts, config = {}, onTransaction, onPrint }: POSInterfaceProps) {
  const [cart, setCart] = useState<CartItem[]>([])
  const [activeCategory, setActiveCategory] = useState("BEBIDAS")
  const [openTabs, setOpenTabs] = useState(["BEBIDAS"])
  const [showInvoice, setShowInvoice] = useState(false)

  const { taxRate = 0.1, currency = "$", companyName = "VENTAS POS", defaultClient = "CLIENTE GENERAL" } = config

  const categories = ["COMIDAS", "BEBIDAS"]
  const filteredProducts = products.filter((product) => product.category === activeCategory)

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existingItem = prev.find((item) => item.id === product.id)
      if (existingItem) {
        const newQuantity = existingItem.quantity + 1
        const subtotal = product.price * newQuantity
        const discount = 0
        const tax = subtotal * taxRate
        const total = subtotal - discount + tax

        return prev.map((item) =>
          item.id === product.id ? { ...item, quantity: newQuantity, subtotal, tax, total } : item,
        )
      }

      const subtotal = product.price
      const discount = 0
      const tax = subtotal * taxRate
      const total = subtotal - discount + tax

      return [
        ...prev,
        {
          id: product.id,
          name: product.name,
          price: product.price,
          quantity: 1,
          image: product.image,
          subtotal,
          discount,
          tax,
          total,
        },
      ]
    })
  }

  const openTab = (category: string) => {
    if (!openTabs.includes(category)) {
      setOpenTabs([...openTabs, category])
    }
    setActiveCategory(category)
  }

  const closeTab = (category: string) => {
    const newTabs = openTabs.filter((tab) => tab !== category)
    setOpenTabs(newTabs)
    if (activeCategory === category && newTabs.length > 0) {
      setActiveCategory(newTabs[0])
    }
  }

  const getCartTotals = () => {
    const subtotal = cart.reduce((sum, item) => sum + item.subtotal, 0)
    const discount = cart.reduce((sum, item) => sum + item.discount, 0)
    const tax = cart.reduce((sum, item) => sum + item.tax, 0)
    const total = cart.reduce((sum, item) => sum + item.total, 0)

    return { subtotal, discount, tax, total }
  }

  const totals = getCartTotals()

  const handlePrint = () => {
    if (onPrint) {
      onPrint(cart, totals)
    } else {
      console.log("[v0] Print transaction:", { cart, totals })
    }
  }

  const handleCancel = () => {
    setCart([])
  }

  const handleTransaction = () => {
    if (onTransaction) {
      onTransaction(cart, totals)
    }
    setCart([])
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="bg-gray-600 flex items-center h-12 sm:h-16 px-2 sm:px-4">
        <div className="flex overflow-x-auto">
          {categories.map((category) => (
            <div key={category} className="flex flex-shrink-0">
              <Button
                variant={activeCategory === category ? "default" : "ghost"}
                className={`h-10 sm:h-16 px-3 sm:px-6 rounded-none flex items-center gap-1 sm:gap-2 text-xs sm:text-sm ${
                  activeCategory === category ? "bg-gray-500 text-white" : "bg-gray-600 text-gray-300 hover:bg-gray-500"
                }`}
                onClick={() => {
                  if (!openTabs.includes(category)) {
                    setOpenTabs([...openTabs, category])
                  }
                  setActiveCategory(category)
                }}
              >
                <div className="w-4 h-4 sm:w-6 sm:h-6 bg-orange-500 rounded flex items-center justify-center text-xs">
                  {category === "COMIDAS" ? "🍔" : "🥤"}
                </div>
                <span className="hidden sm:inline">{category}</span>
                <span className="sm:hidden">{category.slice(0, 3)}</span>
              </Button>
              {openTabs.includes(category) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-10 sm:h-16 w-8 sm:w-12 rounded-none bg-red-500 hover:bg-red-600 text-white"
                  onClick={() => {
                    const newTabs = openTabs.filter((tab) => tab !== category)
                    setOpenTabs(newTabs)
                    if (activeCategory === category && newTabs.length > 0) {
                      setActiveCategory(newTabs[0])
                    }
                  }}
                >
                  <X className="h-3 w-3 sm:h-4 sm:w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2 sm:gap-4">
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden text-white hover:bg-gray-500"
            onClick={() => setShowInvoice(!showInvoice)}
          >
            <Menu className="h-4 w-4" />
          </Button>
          <span className="text-white font-semibold text-xs sm:text-sm hidden sm:inline">{companyName}</span>
          <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white">
            <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full border-2 border-current flex items-center justify-center text-xs">
              ⏻
            </div>
          </Button>
        </div>
      </div>

      <div className="flex flex-1 relative">
        <div className={`flex-1 p-2 sm:p-4 ${showInvoice ? "hidden lg:block" : "block"}`}>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 sm:gap-4">
            {filteredProducts.map((product) => (
              <Card
                key={product.id}
                className="cursor-pointer hover:shadow-md transition-shadow bg-white"
                onClick={() => addToCart(product)}
              >
                <CardContent className="p-2 sm:p-4 text-center relative">
                  <img
                    src={product.image || "/placeholder.svg"}
                    alt={product.name}
                    className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 mx-auto mb-2 rounded object-cover"
                  />
                  <div className="absolute top-1 right-1 sm:top-2 sm:right-2 bg-black text-white text-sm sm:text-lg font-bold w-6 h-6 sm:w-8 sm:h-8 rounded flex items-center justify-center">
                    {product.displayNumber}
                  </div>
                  <div className="mt-2">
                    <div className="bg-green-500 text-white text-xs py-1 px-1 sm:px-2 rounded mb-1 truncate">
                      {product.name}
                    </div>
                    <div className="bg-green-400 h-1 sm:h-2 rounded-full">
                      <div
                        className="bg-green-600 h-1 sm:h-2 rounded-full"
                        style={{ width: `${Math.min(100, (product.stock / 30) * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div
          className={`
          ${showInvoice ? "fixed inset-0 z-50 lg:relative lg:inset-auto" : "hidden lg:block"}
          w-full lg:w-[400px] xl:w-[500px] bg-white border-l border-gray-300 flex flex-col
        `}
        >
          <div className="lg:hidden flex justify-between items-center p-2 bg-gray-100 border-b">
            <span className="font-semibold">Factura</span>
            <Button variant="ghost" size="sm" onClick={() => setShowInvoice(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="p-3 sm:p-4 border-b border-gray-300 bg-gray-50">
            <div className="space-y-2">
              <div className="flex justify-between text-xs sm:text-sm font-semibold">
                <span>FACTURA DE VENTA</span>
                <span>
                  #
                  {Math.floor(Math.random() * 10000)
                    .toString()
                    .padStart(4, "0")}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span>Fecha: {new Date().toLocaleDateString("es-CO")}</span>
                <span>Hora: {new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
              <div className="text-xs">
                <div>Cliente: {defaultClient}</div>
                <div>Vendedor: Usuario Sistema</div>
              </div>
            </div>
          </div>

          <div className="bg-gray-600 text-white text-xs">
            <div className="grid grid-cols-8 lg:grid-cols-10 gap-1 p-2">
              <div className="text-center">#</div>
              <div className="col-span-2 lg:col-span-3 text-left">Producto</div>
              <div className="text-center">Cant</div>
              <div className="text-center">Precio</div>
              <div className="text-center">Subtotal</div>
              <div className="text-center hidden lg:block">Desc</div>
              <div className="text-center hidden lg:block">IVA</div>
              <div className="text-center">Total</div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {cart.map((item, index) => (
              <div
                key={item.id}
                className="grid grid-cols-8 lg:grid-cols-10 gap-1 p-2 text-xs border-b border-gray-200 hover:bg-gray-50"
              >
                <div className="text-center font-medium">{index + 1}</div>
                <div className="col-span-2 lg:col-span-3 text-left font-medium truncate">{item.name}</div>
                <div className="text-center">{item.quantity}</div>
                <div className="text-center">
                  {currency}
                  {item.price.toLocaleString()}
                </div>
                <div className="text-center">
                  {currency}
                  {item.subtotal.toLocaleString()}
                </div>
                <div className="text-center hidden lg:block">
                  {currency}
                  {item.discount.toLocaleString()}
                </div>
                <div className="text-center hidden lg:block">
                  {currency}
                  {Math.round(item.tax).toLocaleString()}
                </div>
                <div className="text-center font-medium">
                  {currency}
                  {Math.round(item.total).toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-300 p-3 bg-gray-50">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span className="font-medium">
                  {currency}
                  {totals.subtotal.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Descuento:</span>
                <span className="font-medium">
                  {currency}
                  {totals.discount.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>IVA (10%):</span>
                <span className="font-medium">
                  {currency}
                  {Math.round(totals.tax).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>TOTAL:</span>
                <span>
                  {currency}
                  {Math.round(totals.total).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gray-600 text-white p-3">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-2 sm:gap-0">
              <Button
                variant="secondary"
                size="sm"
                className="bg-yellow-500 text-black hover:bg-yellow-600 w-full sm:w-auto"
                onClick={handleCancel}
              >
                Cancelar
              </Button>
              <div className="flex gap-2 w-full sm:w-auto">
                <Button
                  size="sm"
                  className="bg-green-600 hover:bg-green-700 flex-1 sm:flex-none"
                  onClick={handleTransaction}
                >
                  <span className="hidden sm:inline">Procesar Venta</span>
                  <span className="sm:hidden">Procesar</span>
                </Button>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 flex-1 sm:flex-none" onClick={handlePrint}>
                  <Printer className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Imprimir</span>
                  <span className="sm:hidden">Print</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default POSInterface
