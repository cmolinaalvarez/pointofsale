export function SpanishDate() {
  const ahora = new Date();
  
  const opciones = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'America/Bogota',
    timeZoneName: 'short'
  };

  return new Intl.DateTimeFormat('es-CO', opciones).format(ahora);
}

// Opción simplificada sin segundos
export function obtenerFechaActualCorta() {
  const ahora = new Date();
  
  const opciones = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/Bogota',
    hour12: true // para usar a.m./p.m.
  };

  return new Intl.DateTimeFormat('es-CO', opciones).format(ahora);
}