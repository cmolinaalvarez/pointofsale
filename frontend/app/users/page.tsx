import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Edit, Trash2 } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/hooks/useAuth";

const users = [
  { id: 1, name: "Juan Pérez", email: "juan@example.com", role: "Administrador", status: "Activo" },
  { id: 2, name: "María García", email: "maria@example.com", role: "Vendedor", status: "Activo" },
  { id: 3, name: "Carlos López", email: "carlos@example.com", role: "Vendedor", status: "Inactivo" },
]

export default function UsersPage() {
  const { token } = useAuth();
  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <span className="text-lg font-semibold">Acceso restringido. Inicia sesión para ver los usuarios.</span>
      </div>
    );
  }
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
          <p className="text-gray-600">Gestión de usuarios del sistema</p>
        </div>
        <Link href="/users/create">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Nuevo Usuario
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Usuarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Nombre</th>
                  <th className="text-left py-2">Email</th>
                  <th className="text-left py-2">Rol</th>
                  <th className="text-left py-2">Estado</th>
                  <th className="text-left py-2">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b">
                    <td className="py-2">{user.name}</td>
                    <td className="py-2">{user.email}</td>
                    <td className="py-2">{user.role}</td>
                    <td className="py-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          user.status === "Activo" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        }`}
                      >
                        {user.status}
                      </span>
                    </td>
                    <td className="py-2">
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
