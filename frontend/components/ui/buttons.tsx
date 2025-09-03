import React from 'react';
import { CheckCircle2, Circle } from 'lucide-react';

// Botón base reutilizable
interface BaseButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'uno' | 'accion' | 'estado';
  active?: boolean; // para estado
}

const baseStyles = {
  uno: 'p-2 rounded bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed',
  accion: 'p-1 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 disabled:opacity-40',
  estado: 'group inline-flex items-center justify-center rounded-full p-1 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 disabled:opacity-40'
};

export const BotonUno: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className = '', ...props }) => (
  <button {...props} className={`${baseStyles.uno} ${className}`.trim()} />
);

export const BotonAccion: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className = '', ...props }) => (
  <button {...props} className={`${baseStyles.accion} ${className}`.trim()} />
);

interface BotonEstadoProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  active: boolean;
  titleWhenActive?: string;
  titleWhenInactive?: string;
}

export const BotonEstado: React.FC<BotonEstadoProps> = ({ active, titleWhenActive = 'Desactivar', titleWhenInactive = 'Activar', className = '', ...props }) => (
  <button
    aria-label={active ? titleWhenActive : titleWhenInactive}
    title={active ? titleWhenActive : titleWhenInactive}
    {...props}
    className={`${baseStyles.estado} ${className}`.trim()}
  >
    {active ? (
      <CheckCircle2 className="h-5 w-5 text-green-600 group-hover:text-green-700" />
    ) : (
      <Circle className="h-5 w-5 text-gray-400 group-hover:text-gray-500" />
    )}
  </button>
);



// Alias semánticos (si se quieren usar los nombres exactos mencionados)
export const BotonUnoPrimary = BotonUno; // por si se requiere otro nombre
