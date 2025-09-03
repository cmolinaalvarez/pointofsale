import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, Package, Warehouse, Users } from "lucide-react"

const stats = [
  {
    title: "Nuevos Pedidos",
    value: "150",
    icon: <TrendingUp className="w-6 h-6" />,
    color: "bg-blue-500",
    textColor: "text-blue-600",
  },
  {
    title: "Productos Vendidos",
    value: "2,340",
    icon: <Package className="w-6 h-6" />,
    color: "bg-green-500",
    textColor: "text-green-600",
  },
  {
    title: "Bodegas Activas",
    value: "12",
    icon: <Warehouse className="w-6 h-6" />,
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
  },
  {
    title: "Usuarios Activos",
    value: "65",
    icon: <Users className="w-6 h-6" />,
    color: "bg-red-500",
    textColor: "text-red-600",
  },
]

export function DashboardStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {stats.map((stat, index) => (
        <Card key={index} className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">{stat.title}</CardTitle>
            <div className={`p-2 rounded-lg ${stat.color} text-white`}>{stat.icon}</div>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stat.textColor}`}>{stat.value}</div>
            <p className="text-xs text-gray-500 mt-1">+12% desde el mes pasado</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
