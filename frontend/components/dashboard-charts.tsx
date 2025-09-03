"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts"

const salesByProduct = [
  { name: "Producto A", ventas: 4000 },
  { name: "Producto B", ventas: 3000 },
  { name: "Producto C", ventas: 2000 },
  { name: "Producto D", ventas: 2780 },
  { name: "Producto E", ventas: 1890 },
]

const salesByWarehouse = [
  { name: "Bodega 1", ventas: 2400 },
  { name: "Bodega 2", ventas: 1398 },
  { name: "Bodega 3", ventas: 9800 },
  { name: "Bodega 4", ventas: 3908 },
]

const monthlySales = [
  { mes: "Ene", ventas: 4000 },
  { mes: "Feb", ventas: 3000 },
  { mes: "Mar", ventas: 2000 },
  { mes: "Abr", ventas: 2780 },
  { mes: "May", ventas: 1890 },
  { mes: "Jun", ventas: 2390 },
]

const salesByUser = [
  { name: "Juan Pérez", value: 400, color: "#0088FE" },
  { name: "María García", value: 300, color: "#00C49F" },
  { name: "Carlos López", value: 300, color: "#FFBB28" },
  { name: "Ana Martínez", value: 200, color: "#FF8042" },
]

export function DashboardCharts() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
      <Card className="w-full">
        <CardHeader className="pb-2 sm:pb-6">
          <CardTitle className="text-sm sm:text-base lg:text-lg">Ventas por Producto</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
            <BarChart data={salesByProduct} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-45} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="ventas" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader className="pb-2 sm:pb-6">
          <CardTitle className="text-sm sm:text-base lg:text-lg">Ventas por Bodega</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
            <BarChart data={salesByWarehouse} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-45} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="ventas" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader className="pb-2 sm:pb-6">
          <CardTitle className="text-sm sm:text-base lg:text-lg">Ventas Totales por Mes</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
            <LineChart data={monthlySales} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="ventas" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader className="pb-2 sm:pb-6">
          <CardTitle className="text-sm sm:text-base lg:text-lg">Ventas por Usuario</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
            <PieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <Pie
                data={salesByUser}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name.split(" ")[0]} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {salesByUser.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
