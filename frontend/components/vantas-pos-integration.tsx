"use client"

import POSInterface, { type Product, type CartItem, type POSConfig } from "./pos-interface"

interface VentasPOSProps {
  storeId?: string
  userId?: string
  products?: Product[]
  onSale?: (transaction: any) => void
}

export function VentasPOS({ storeId, userId, products, onSale }: VentasPOSProps) {
  const config: POSConfig = {
    taxRate: 0.19, // Colombian IVA
    currency: "$",
    companyName: "VENTAS POS",
    defaultClient: "CLIENTE GENERAL",
  }

  const handleTransaction = (cart: CartItem[], totals: any) => {
    const transaction = {
      id: Date.now().toString(),
      storeId,
      userId,
      items: cart,
      totals,
      timestamp: new Date().toISOString(),
      status: "completed",
    }

    if (onSale) {
      onSale(transaction)
    }

    console.log("[VNTAS] Transaction completed:", transaction)
  }

  const handlePrint = (cart: CartItem[], totals: any) => {
    console.log("[VENTAS] Printing receipt:", { cart, totals })
    // Integration with  printing system
  }

  return <POSInterface products={products} config={config} onTransaction={handleTransaction} onPrint={handlePrint} />
}

export default VentasPOS
