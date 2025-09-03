import { DashboardStats } from "@/components/dashboard-stats"
import { DashboardCharts } from "@/components/dashboard-charts"

// Página principal por defecto (ruta "/")
export default function HomePage() {
  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Panel de control del sistema de ventas</p>
      </div>

      <DashboardStats />
      <DashboardCharts />
    </div>
  );
}
