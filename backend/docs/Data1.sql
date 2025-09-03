Por favor validar si cumplo con todas las validaciones de datos y de ciberseguridad en en Backen para el modelo payment_terms
 

# app/models/payment_term.py
# =============================================================================
# MODELO: PaymentTerm (Condiciones de Pago)
# -----------------------------------------------------------------------------
# Este modelo representa una "condición de pago" reutilizable que puede asociarse
# a compras/ventas para determinar fecha de vencimiento (due_date) y ventana de
# pronto pago (discount_until).
# =============================================================================

import enum
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

# SQLAlchemy imports
from sqlalchemy import Enum as SAEnum, String, Integer, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

# Base de datos
from app.db.base import Base  # Declarative Base (tu base ORM asíncrona)


class PaymentBasisEnum(enum.Enum):
    """
    Enumeración para las bases de cálculo de fechas de pago.
    
    Define los dos métodos posibles para calcular fechas de vencimiento:
    
    Attributes:
        INVOICE_DATE: Base de cálculo desde la fecha del documento (factura)
        END_OF_MONTH: Base de cálculo desde el fin de mes del documento
    """
    INVOICE_DATE = "Factura"    # Base: fecha de la factura (ej: fecha factura + 30 días)
    END_OF_MONTH = "Fin de més" # Base: fin de mes del documento (ej: fin de mes + 30 días)


class PaymentTerm(Base):
    """
    Modelo que representa una condición de pago en el sistema.
    
    Una condición de pago define los términos y plazos para el pago de facturas,
    incluyendo descuentos por pronto pago y la base para calcular fechas de vencimiento.
    """
    
    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE LA TABLA
    # -------------------------------------------------------------------------
    __tablename__ = "payment_terms"  # Nombre físico de la tabla en la base de datos

    # -------------------------------------------------------------------------
    # IDENTIFICACIÓN PRINCIPAL
    # -------------------------------------------------------------------------
    
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),          # Tipo PostgreSQL UUID, manejado como objeto UUID en Python
        primary_key=True,               # Esta columna es la llave primaria de la tabla
        default=uuid.uuid4,             # Genera automáticamente UUID v4 al crear un nuevo registro
        comment="Identificador único universal (UUIDv4) como llave primaria. "
                "Ventajas: evita colisiones entre nodos/servicios, útil en microservicios."
    )
    
    code: Mapped[str] = mapped_column(
        String(50),                     # Tipo string con longitud máxima de 50 caracteres
        unique=True,                    # Garantiza que no existan dos registros con el mismo código
        index=True,                     # Crea índice para búsquedas rápidas por este campo
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        comment="Código único para identificación rápida (ej. NET30, CASH). "
                "Indexado para optimización de consultas. "
                "String(50) es suficiente para códigos cortos (ajústalo si tu negocio requiere más)."
    )
    
    name: Mapped[str] = mapped_column(
        String(255),                    # Tipo string con longitud máxima de 255 caracteres
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        unique=True,                    # Garantiza que no existan dos registros con el mismo nombre
        comment="Nombre descriptivo de la condición de pago. Debe ser único en el sistema. "
                "Ejemplos: 'Contado', 'Crédito 30 días', '2/10 Net 30'."
    )
    
    description: Mapped[str] = mapped_column(
        String(255),                    # Tipo string con longitud máxima de 255 caracteres
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        comment="Descripción detallada de los términos de pago para contexto del usuario. "
                "String(255) es típico; aumenta si esperas descripciones más largas. "
                "Ejemplo: '2% de descuento si paga dentro de 10 días, neto 30 días'."
    )

    # -------------------------------------------------------------------------
    # TÉRMINOS DE PAGO Y DESCUENTOS
    # -------------------------------------------------------------------------
    
    net_days: Mapped[int] = mapped_column(
        Integer,                        # Tipo entero para almacenar días
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        default=0,                      # Valor por defecto: 0 días (contado)
        comment="Número de días para el vencimiento del pago desde la fecha base. "
                "0 = contado inmediato. "
                "Ejemplo: 30 días para NET30, 60 días para NET60."
    )

    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),                  # Tipo numérico con precisión: 5 dígitos totales, 2 decimales
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        default=0,                      # Valor por defecto: 0% de descuento
        comment="Porcentaje de descuento por pronto pago (0-100). Precisión decimal de 2 dígitos. "
                "Numeric(5,2) permite valores de -999.99 a 999.99. "
                "En la práctica, se espera 0..100. Si quieres reforzar esa regla, "
                "puedes añadir una CHECK CONSTRAINT a nivel de tabla."
    )

    discount_days: Mapped[int] = mapped_column(
        Integer,                        # Tipo entero para almacenar días
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        default=0,                      # Valor por defecto: 0 días (sin descuento)
        comment="Ventana de días para aplicar el descuento desde la fecha base. "
                "0 = sin descuento. "
                "Ejemplo: 10 días para 2/10/NET30 (descuento del 2% si se paga en 10 días)."
    )
    
    basis: Mapped[PaymentBasisEnum] = mapped_column(
        SAEnum(
            PaymentBasisEnum,           # Enum de SQLAlchemy basado en PaymentBasisEnum
            name="payment_basis_enum",  # Nombre del tipo ENUM en PostgreSQL
            native_enum=True,           # Usa el tipo ENUM nativo de PostgreSQL
            validate_strings=True       # Valida que los strings coincidan con los valores del enum
        ),
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        default=PaymentBasisEnum.INVOICE_DATE,  # Valor por defecto: fecha de factura
        comment="Base de cálculo para fechas: 'Factura' (fecha documento) o 'Fin de més' (fin de mes documento). "
                "Con esto podrás calcular due_date y discount_until en tu lógica de negocio. "
                "Ejemplo: 'Factura' = desde fecha factura, 'Fin de més' = desde fin de mes."
    )

    # -------------------------------------------------------------------------
    # METADATOS Y AUDITORÍA
    # -------------------------------------------------------------------------
    
    active: Mapped[bool] = mapped_column(
        Boolean,                        # Tipo booleano (TRUE/FALSE)
        default=True,                   # Valor por defecto: True (activo)
        comment="Indica si el término de pago está activo (true) o inactivo (false). "
                "Útil para soft-delete o deshabilitar términos sin eliminarlos físicamente."
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),          # Tipo PostgreSQL UUID, manejado como objeto UUID en Python
        ForeignKey("users.id"),         # Llave foránea que referencia la tabla users, columna id
        nullable=False,                 # El campo no puede ser NULL en la base de datos
        comment="Llave foránea que referencia al usuario que creó este término de pago. "
                "Garantiza trazabilidad de quién creó cada condición de pago."
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,                       # Tipo datetime para almacenar fecha y hora
        default=datetime.utcnow,        # Valor por defecto: fecha/hora actual en UTC
        comment="Marca de tiempo de creación del registro (UTC). "
                "Se establece automáticamente al crear. "
                "Usa datetime.utcnow() (naive). Si tu aplicación es TZ-aware, "
                "considera usar timestamps con zona o normalizar siempre a UTC."
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,                       # Tipo datetime para almacenar fecha y hora
        onupdate=datetime.utcnow,       # Se actualiza automáticamente al modificar el registro
        nullable=True,                  # Puede ser NULL para registros nunca actualizados
        comment="Marca de tiempo de última actualización (UTC). "
                "Se actualiza automáticamente al modificar el registro. "
                "Nullable para registros que nunca han sido actualizados."
    )
    
    # -------------------------------------------------------------------------
    # MÉTODOS DE UTILIDAD (SIN DEPENDENCIAS EXTERNAS)
    # -------------------------------------------------------------------------
    
    def __repr__(self) -> str:
        """
        Representación formal del objeto para debugging y logging.
        
        Returns:
            str: Representación string del objeto PaymentTerm
        """
        return f"<PaymentTerm(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    def calculate_due_date(self, invoice_date: datetime) -> datetime:
        """
        Calcula la fecha de vencimiento basada en la fecha de factura y los términos.
        
        Esta implementación no requiere dependencias externas y usa solo
        la biblioteca estándar de Python.
        
        Args:
            invoice_date: Fecha de la factura/documento
            
        Returns:
            datetime: Fecha de vencimiento calculada según net_days y basis
        """
        if self.basis == PaymentBasisEnum.INVOICE_DATE:
            # Cálculo directo desde fecha de factura: simplemente sumar los días netos
            return invoice_date + timedelta(days=self.net_days)
        else:
            # Cálculo desde fin de mes (EOM - End of Month)
            # Estrategia: encontrar el primer día del mes siguiente y restar 1 día
            # para obtener el último día del mes actual
            if invoice_date.month == 12:
                # Caso especial: diciembre -> el siguiente mes es enero del año siguiente
                next_month = invoice_date.replace(
                    year=invoice_date.year + 1,  # Incrementar el año
                    month=1,                     # Primer mes (enero)
                    day=1                        # Primer día del mes
                )
            else:
                # Mes normal: simplemente incrementar el mes
                next_month = invoice_date.replace(
                    month=invoice_date.month + 1,  # Mes siguiente
                    day=1                          # Primer día del mes
                )
            
            # El último día del mes actual es el día anterior al primer día del mes siguiente
            end_of_month = next_month - timedelta(days=1)
            
            # Sumar los días netos al fin de mes
            return end_of_month + timedelta(days=self.net_days)
    
    def calculate_discount_deadline(self, invoice_date: datetime) -> Optional[datetime]:
        """
        Calcula la fecha límite para aplicar el descuento por pronto pago.
        
        Args:
            invoice_date: Fecha de la factura/documento
            
        Returns:
            datetime: Fecha límite para el descuento, o None si no aplica descuento
        """
        # Si no hay descuento configurado, retornar None
        if self.discount_days == 0 or self.discount_percent == 0:
            return None
            
        # Lógica similar a calculate_due_date pero para discount_days
        if self.basis == PaymentBasisEnum.INVOICE_DATE:
            # Cálculo desde fecha de factura
            return invoice_date + timedelta(days=self.discount_days)
        else:
            # Cálculo desde fin de mes
            if invoice_date.month == 12:
                next_month = invoice_date.replace(
                    year=invoice_date.year + 1,
                    month=1,
                    day=1
                )
            else:
                next_month = invoice_date.replace(
                    month=invoice_date.month + 1,
                    day=1
                )
            
            end_of_month = next_month - timedelta(days=1)
            return end_of_month + timedelta(days=self.discount_days)

    def is_discount_applicable(self, invoice_date: datetime, payment_date: datetime) -> bool:
        """
        Verifica si un descuento por pronto pago es aplicable.
        
        Args:
            invoice_date: Fecha de la factura/documento
            payment_date: Fecha de pago propuesta
            
        Returns:
            bool: True si el descuento aplica, False en caso contrario
        """
        discount_deadline = self.calculate_discount_deadline(invoice_date)
        return discount_deadline is not None and payment_date <= discount_deadline

# =============================================================================
# NOTAS ADICIONALES:
# -----------------------------------------------------------------------------
# 1. Las restricciones CHECK para validar discount_percent (0-100) y net_days (≥0)
#    pueden añadirse a nivel de base de datos para mayor robustez.
# 2. Considerar añadir índices adicionales si se filtran frecuentemente por
#    user_id o active.
# 3. Para aplicaciones distribuidas, considerar usar timezone-aware timestamps
#    en lugar de datetime.utcnow().
# 4. Los métodos calculate_due_date y calculate_discount_deadline usan solo
#    la biblioteca estándar de Python, sin dependencias externas.
# =============================================================================