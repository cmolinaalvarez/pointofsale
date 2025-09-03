# =============================================================================
# MÓDULO DE ENDPOINTS PARA "ENTRIES" (MOVIMIENTOS/COMPROBANTES)
# =============================================================================
# ⚙️ Objetivo:
#   - CRUD básico (crear, listar, leer por ID, desactivar, patch)
#   - Importación masiva desde CSV con tolerancia a errores por fila y un
#     único registro de auditoría al final.
#
# 🧩 Puntos clave de diseño:
#   - SQLAlchemy AsyncSession (async/await) + transacciones y SAVEPOINT por fila.
#   - Validación estricta de document_id como UUID (formato) y existencia en DB.
#   - Numeración por documento y año con prefijo configurable por documento.
#   - Re-cálculo de stock "absoluto" (compras - salidas) al final (delta=0).
#   - Auditoría granular en CRUD y agregada en importación masiva.
#
# 📝 Convenciones:
#   - Comentarios extensos para cada bloque y líneas sensibles.
#   - No se modifica la lógica original; solo se documenta en detalle.
# =============================================================================

# ------------------------------
# IMPORTS DEL ECOSISTEMA
# ------------------------------
from sqlalchemy import select, func          # select() para consultas, func.* para funciones SQL (MAX, COALESCE, DATE_PART, etc.)
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
#  - APIRouter: agrupa rutas bajo un prefijo y etiquetas.
#  - Depends: inyección de dependencias (DB, usuario actual, etc.).
#  - HTTPException: excepciones HTTP con status code controlado.
#  - status: enumeraciones de códigos de estado HTTP.
#  - Query: define y valida parámetros query (skip, limit).
#  - UploadFile, File: manejo de archivos subidos (CSV).

from sqlalchemy.ext.asyncio import AsyncSession  # Sesión asíncrona de SQLAlchemy (CRUD no bloqueante).
from sqlalchemy.exc import IntegrityError, SQLAlchemyError  # Errores específicos de SQLAlchemy para manejo granular.

from uuid import UUID                       # Tipo fuerte para path params (valida que sea UUID válido).
from typing import List, Optional           # Tipados de listas y opcionales (para FastAPI y pydantic).
import logging                              # Logging estructurado para diagnóstico y auditoría técnica.

# ------------------------------
# IMPORTS DE LA APLICACIÓN
# ------------------------------
from app.core.security import get_async_db  # Proveedor de AsyncSession (inyección FastAPI).
from app.models.user import User            # Modelo de usuario (para tipos y acceso a su id).

# Utilidades estándar
import csv, json, re                        # csv: parseo de CSV; json: parseo de items; re: regex UUID.
from io import StringIO                     # Buffer de texto (convierte bytes -> archivo-like para csv).
from decimal import Decimal                 # Decimal para montos exactos (evita errores de punto flotante).
from datetime import datetime               # Timestamps (created_at, parsing ISO).

# 👇 (Este Optional está importado nuevamente; es redundante pero inofensivo)
from typing import Optional

# Modelos de dominio
from app.models.document import Document    # Documento (define prefijo y existencia del tipo de comprobante).
from app.models.purchase import Purchase, PurchaseItem  # Cabecera y detalle (ítems) del movimiento.

# Auditoría (nivel + registro)
from app.utils.audit_level import get_audit_level  # Determina si auditar y con qué granularidad.
from app.utils.audit import log_action              # Inserta eventos de auditoría.

# Stock
from app.helper.stock import adjust_stock_quantity  # Recalcula/ajusta stock (se invoca con delta=0 para recalcular absoluto).

# Esquemas (pydantic) para compra/salida de API
from app.schemas.purchase import (
    PurchaseCreate,
    PurchaseRead,
)

# CRUD de purchases (capa de acceso a datos con reglas específicas)
from app.crud.purchase import (
    create_purchase,
    get_purchases,
    get_purchase,
    deactivate_purchase_and_return_stock
)
from app.dependencies.auth import get_current_user, require_scopes, current_user_id


# 👇 Importes duplicados (log_action, get_audit_level); redundantes pero sin efecto adverso:
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level

# ------------------------------
# CONFIGURACIÓN DE RUTAS Y LOGGING
# ------------------------------
logger = logging.getLogger(__name__)            # Logger de módulo (hereda nivel/handlers globales).
router = APIRouter(tags=["Purchases"], dependencies=[Depends(get_current_user)])  # Todas las rutas cuelgan de /purchases

# =============================================================================
# CREATE - POST
# =============================================================================
@router.post("/", response_model=PurchaseRead, status_code=201)
async def create_purchase_endpoint(
    purchase_in: PurchaseCreate,                         # Cuerpo del request (validado por pydantic).
    db: AsyncSession = Depends(get_async_db),      # Sesión de DB inyectada.
    uid: str = Depends(current_user_id) # Usuario autenticado (para auditoría y ownership).
):
    """
    Crea una compra (Purchase) usando la capa CRUD.
    Nota: el CRUD realiza el commit internamente para encapsular la operación.
    """
    try:
        # Delegamos la lógica de creación a la capa CRUD (incluye validaciones y commit).
        print("NEW_PURCHASE ::::::::::::::::::::::")
        new_purchase = await create_purchase(db, purchase_in, uid)
        print("NEW_PURCHASE ::::::::::::::::::::::",new_purchase)
        logger.info("Entrada creada: %s por usuario %s", new_purchase.id, uid)
        # Devolvemos el objeto serializado al esquema de respuesta.
        return PurchaseRead.model_validate(new_purchase)

    except IntegrityError as e:
        # Ej.: violación de restricciones (FK/UK/NOT NULL) durante INSERT.
        await db.rollback()  # Rollback defensivo (si hubiera transacción abierta).
        logger.error("Error de integridad al crear compra: %s", e, exc_info=True)
        # Exponemos 400 (bad request) con detalle del origen de la BD.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )

    except SQLAlchemyError as e:
        # Cualquier error interno de SQLAlchemy (conexión, dialécto, etc.).
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear compra: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )

    except Exception as e:
        # Failsafe para errores no contemplados (serialización, lógica, etc.).
        await db.rollback()
        logger.exception("Error interno al crear compra", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# =============================================================================
# GET ALL
# =============================================================================
@router.get("/", response_model=List[PurchaseRead])
async def list_purchases(
    skip: int = Query(0, ge=0),                   # Paginación: índice inicial (>=0).
    limit: int = Query(100, ge=1, le=1000),       # Paginación: cantidad (1..1000).
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    """
    Lista compras (sin 'total' agregado).
    🔎 La capa CRUD podría generar auditoría de GETALL si audit_level > 2.
    💾 Hacemos commit aquí para persistir ese log en caso de que se haya creado.
    """
    try:
        # Obtenemos compras de la capa CRUD, potencialmente filtradas por user_id.
        items = await get_purchases(db, skip=skip, limit=limit, user_id=uid)

        # Importante: si el CRUD hace flush para auditoría, aquí confirmamos con commit.
        await db.commit()

        # Serializamos cada modelo ORM a su esquema de lectura.
        return [PurchaseRead.model_validate(it) for it in items]

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar compras: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos al obtener las compras")

    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar compras", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al obtener las compras")


# =============================================================================
# GET BY ID
# =============================================================================
@router.get("/{purchase_id}", response_model=PurchaseRead)
async def read_purchase(
    purchase_id: UUID,                                  # Path param validado por FastAPI (UUID correcto).
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    """
    Obtiene una compra por ID.
    🔎 La capa CRUD podría auditar GETID si audit_level > 2 (hace flush);
    💾 Hacemos commit para persistir ese evento, si aplica.
    """
    try:
        # Recuperamos la compra; podría aplicar filtros de seguridad por user_id.
        purchase = await get_purchase(db, purchase_id, user_id=uid)

        if not purchase:
            # No existe o no es accesible.
            raise HTTPException(status_code=404, detail="Entrada no encontrada")

        # Confirmamos la auditoría (si se generó).
        await db.commit()

        return PurchaseRead.model_validate(purchase)

    except HTTPException:
        # Si ya formamos una HTTPException (e.g. 404), propagamos tal cual.
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener compra por ID", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al consultar la compra")


# =============================================================================
# DEACTIVATE (PUT) — Soft delete + devolución de stock (según CRUD)
# =============================================================================
@router.put("/{purchase_id}/deactivate", response_model=PurchaseRead)
async def deactivate_purchase(
    purchase_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    """
    Desactiva una compra (soft-delete o marca 'active=False') y retorna el stock resultante.
    La lógica concreta reside en el CRUD `deactivate_purchase_and_return_stock`.
    """
    # La función retorna (purchase, stock_diff) — aquí solo devolvemos la purchase.
    purchase, _ = await deactivate_purchase_and_return_stock(db, purchase_id, user_id=uid)

    if purchase is None:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    # Confirmamos la operación de desactivación y potenciales ajustes de stock.
    await db.commit()

    # Refrescamos la instancia para traer los valores definitivos desde la DB.
    await db.refresh(purchase)

    return purchase


# =============================================================================
# IMPORT MASSIVE ENTRIES (CSV) — UN SOLO LOG IMPORT
# =============================================================================
# Este bloque implementa un endpoint para importar "purchases" desde un CSV.
# - Valida que cada fila tenga un document_id con formato UUID.
# - Bloquea (SELECT ... FOR UPDATE) el documento para asegurar consistencia al asignar secuencias.
# - Calcula la secuencia por (documento, año) y arma un "purchase_number" con prefijo.
# - Inserta la cabecera (Purchase) y los ítems (PurchaseItem) de cada fila.
# - Recalcula stock para cada par (warehouse_id, product_id) afectado.
# - Usa SAVEPOINT por fila para ser tolerante a errores: si una fila falla, el resto continúa.
# - Emite un único log/auditoría al final con el resumen de la importación.

# ------------------------------
# Utilidades de validación y formateo
# ------------------------------

# Regex para validar UUID estándar (8-4-4-4-12 dígitos hex).
#   ^ y $ fuerzan coincidencia completa (no parcial).
#   [0-9a-fA-F] permite mayúsculas o minúsculas.
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

def _parse_iso_dt(s: Optional[str]) -> datetime:
    """
    Convierte una cadena ISO-8601 a datetime.
    Reglas:
      - Si s es None o vacío → datetime.utcnow() (marca de tiempo actual).
      - Reemplaza 'Z' (Zulu/UTC) por '+00:00' para que `fromisoformat` lo acepte.
      - Si falla el parseo por formato inesperado → fallback a utcnow().
    Ejemplos aceptados:
      '2025-08-17T12:34:56Z', '2025-08-17 12:34:56+00:00', '2025-08-17'
    """
    if not s:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        # ⚠️ Si esperas fechas con locales (p.ej. '17/08/2025'), conviértelas antes del import.
        return datetime.utcnow()

def _build_doc_number(prefix: str, year: int, sequence: int) -> str:
    """
    Construye el código visible de la compra con el formato:
      <prefix opcional terminado en '-'><año>-<secuencia 5 dígitos>
    Ejemplo: 'FAC-2025-00042' o '2025-00042' si no hay prefijo.
    """
    p = (prefix or "").strip()
    if p and not p.endswith("-"):
        p += "-"
    return f"{p}{year}-{sequence:05d}"


# =============================================================================
# IMPORT MASIVO — ENDPOINT
# =============================================================================
# =============================================================================
# IMPORT MASIVO — ENDPOINT (TODO-O-NADA + LISTA COMPLETA DE ERRORES)
# =============================================================================
@router.post("/import", status_code=201)
async def import_purchases(
    file: UploadFile = File(...),                     # CSV subido por el cliente.
    db: AsyncSession = Depends(get_async_db),         # Sesión asíncrona.
    uid: str = Depends(current_user_id),   # Usuario actual (para ownership/auditoría).
):
    try:
        # 1) Leemos bytes del archivo y los decodificamos como UTF-8.
        #    Si el CSV no está en UTF-8, conviene recodificarlo previamente.
        content = await file.read()
        reader = csv.DictReader(StringIO(content.decode("utf-8")))

        # 2) Normalizamos headers (DictReader usa la primera línea como claves del dict por fila):
        #    - strip() para quitar espacios accidentalmente agregados.
        #    - reemplazo del BOM (\ufeff) que a veces viene en CSV exportados desde Excel.
        if reader.fieldnames:
            reader.fieldnames = [h.strip().replace("\ufeff", "") for h in reader.fieldnames]
            logger.info("Headers después de limpieza: %s", reader.fieldnames)

        # 3) Estructuras de cache para eficiencia durante el bucle:
        #    - seq_counter[(doc_id, year)] → última secuencia encontrada/usada para ese par.
        #    - dt_prefix[doc_id] → prefijo del documento (evita reconsultar en DB).
        seq_counter: dict[tuple[str, int], int] = {}
        dt_prefix: dict[str, str] = {}

        async def ensure_counter_for_uuid(doc_id_str: str, year: int) -> tuple[str, str]:
            """
            Valida y prepara el contexto de numeración para (documento, año).
            Pasos:
              (a) Verifica que doc_id_str tenga formato de UUID (no solo existencias).
              (b) Hace SELECT ... FOR UPDATE del Document para:
                  - asegurar que existe,
                  - serializar la asignación de secuencias (evita condiciones de carrera).
              (c) Inicializa en caché el contador de secuencia (busca MAX en DB) y el prefix.
              (d) Devuelve (doc_id como str, prefix).
            """
            # (a) Validación de formato (no convierte a UUID aquí; solo regex).
            if not _UUID_RE.match(doc_id_str):
                # Si la fuente "siempre" entrega UUID, este error indica datos corruptos en el CSV.
                raise HTTPException(status_code=400, detail=f"document_id no es UUID: {doc_id_str}")

            # (b) Lock pesimista del Document: evita que dos procesos asignen la misma secuencia simultáneamente.
            res = await db.execute(
                select(Document).where(Document.id == doc_id_str).with_for_update()
            )
            doc = res.scalar_one_or_none()
            if not doc:
                # Puede ser un ID inexistente o un documento no accesible por políticas de seguridad.
                raise HTTPException(status_code=400, detail=f"document_id inválido: {doc_id_str}")

            # Normalizamos el ID a str (por si el ORM lo trae como UUID nativo).
            doc_id = str(doc.id)
            key = (doc_id, year)

            # Reutilizamos el contador si ya se inicializó en esta corrida.
            if key in seq_counter:
                return doc_id, dt_prefix[doc_id]

            # Cacheamos el prefijo del documento (puede ser "" si es None).
            dt_prefix[doc_id] = doc.prefix or ""

            # (c) Buscamos la secuencia máxima usada para este doc en este año:
            #     MAX(sequence_number) WHERE document_id = doc_id AND YEAR(created_at) = year
            max_res = await db.execute(
                select(func.coalesce(func.max(Purchase.sequence_number), 0)).where(
                    Purchase.document_id == doc_id,
                    func.date_part("year", Purchase.created_at) == year,
                )
            )
            # Guardamos el máximo encontrado (o 0 si no hay registros).
            seq_counter[key] = int(max_res.scalar_one() or 0)

            return doc_id, dt_prefix[doc_id]

        # 4) Métricas y acumuladores de la importación:
        imported = 0                 # Conteo de filas importadas correctamente.
        errors: list[str] = []       # Errores por fila (para devolver en respuesta y log).
        pairs_to_recalc: set[tuple[str, str]] = set()  # (warehouse_id, product_id) para recalcular stock al final.

        # 5) Bucle principal sobre el CSV:
        #    ⚠️ Todo-o-nada:
        #       - Usamos SAVEPOINT por fila para detectar/acumular errores,
        #       - PERO si aparece cualquier error, haremos rollback global al final (no quedará nada aplicado).
        for idx, row in enumerate(reader, start=1):
            # Iniciamos un SAVEPOINT (transacción anidada) para esta fila.
            sp = await db.begin_nested()
            try:
                # 5.1) Validaciones y preparación de datos de cabecera
                doc_id_str = (row.get("document_id") or "").strip()
                if not doc_id_str:
                    # document_id es obligatorio (y exógeno al CSV).
                    raise ValueError("Falta 'document_id' (UUID).")

                # Fecha para determinar el año de numeración; aceptamos 'date' o 'created_at'.
                # Si ninguna está presente → usamos utcnow().
                dt = _parse_iso_dt((row.get("date") or row.get("created_at") or "").strip() or None)
                year = dt.year

                # Preparamos el contador de secuencia y recuperamos el prefijo del documento.
                doc_id, prefix = await ensure_counter_for_uuid(doc_id_str, year)

                # 5.2) Cálculo de secuencia y número visible
                # Incrementamos la última secuencia para este (doc_id, year).
                seq_counter[(doc_id, year)] += 1
                sequence = seq_counter[(doc_id, year)]

                # Construimos el "purchase_number" (ej.: FAC-2025-00001).
                purchase_number = _build_doc_number(prefix, year, sequence)

                # 5.3) Construcción del modelo Purchase (cabecera)
                purchase = Purchase(
                    document_id=doc_id,
                    third_party_id=(row.get("third_party_id") or "").strip(),
                    concept_id=(row.get("concept_id") or "").strip(),
                    user_id=(row.get("user_id") or str(uid)).strip(),
                    sequence_number=sequence,
                    purchase_number=purchase_number,
                    subtotal=Decimal(str(row.get("subtotal", "0"))),
                    discount=Decimal(str(row.get("discount", "0"))),
                    tax=Decimal(str(row.get("tax", "0"))),
                    total=Decimal(str(row.get("total", "0"))),
                    # 'active' tolera varias representaciones de verdadero.
                    active=str(row.get("active", "true")).lower() in ("true", "1", "yes", "si", "sí"),
                    created_at=dt,
                )
                db.add(purchase)  # Agregamos a la sesión; todavía no se persiste hasta flush/commit.

                # 5.4) Ítems (detalle)
                # Dos modalidades:
                #   A) Columna 'items' con JSON de lista de ítems.
                #   B) Columnas planas por fila (product_id, quantity, ...).
                if row.get("items"):
                    # A) Parseamos JSON desde la columna 'items'.
                    items = json.loads(row["items"])
                    if not isinstance(items, list) or not items:
                        raise ValueError("La columna 'items' debe ser una lista no vacía")

                    for it in items:
                        product_id = str(it["product_id"]).strip()  # Obligatorio.

                        db.add(PurchaseItem(
                            purchase=purchase,  # backref: ORM vincula con la cabecera.
                            product_id=product_id,
                            quantity=Decimal(str(it["quantity"])),
                            subtotal=Decimal(str(it.get("subtotal", 0))),
                            discount=Decimal(str(it.get("discount", 0))),
                            tax=Decimal(str(it.get("tax", 0))),
                            total=Decimal(str(it.get("total", 0))),
                        ))
                else:
                    # B) Fila plana: exigimos al menos 'product_id' y 'quantity'.
                    product_id = str(row["product_id"]).strip()
                    db.add(PurchaseItem(
                        purchase=purchase,
                        product_id=product_id,
                        quantity=Decimal(str(row["quantity"])),
                        # Si hay columnas específicas del ítem, las preferimos.
                        # Si no, usamos los totales de la cabecera como fallback.
                        subtotal=Decimal(str(row.get("item_subtotal", row.get("subtotal", 0)))),
                        discount=Decimal(str(row.get("item_discount", row.get("discount", 0)))),
                        tax=Decimal(str(row.get("item_tax", row.get("tax", 0)))),
                        total=Decimal(str(row.get("item_total", row.get("total", 0)))),
                    ))
                    
                # 5.5) Flush dentro del SAVEPOINT:
                #     - Valida constraints antes de confirmar el savepoint.
                #     - Genera IDs y FK en memoria (si aplica).
                await db.flush()

                # 5.6) Confirmamos el SAVEPOINT de la fila (la fila queda "aplicada" en la transacción padre).
                await sp.commit()
                imported += 1

            except Exception as row_err:
                # Si algo falla en la fila, revertimos SOLO lo hecho por esa fila:
                await sp.rollback()
                # Guardamos error detallado (incluye stacktrace en logs).
                logger.warning("Fila con error en importación (fila %d): %s", idx, row_err, exc_info=True)
                errors.append(f"fila {idx}: {row_err}")

        # 6) Regla TODO-O-NADA (parte 1): si ninguna fila fue válida → abortamos.
        if imported == 0:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Importación cancelada: no se encontraron filas válidas.",
                    "errors": errors or ["CSV vacío o todas las filas inválidas."]
                },
            )

        # 6.1) Regla TODO-O-NADA (parte 2): si hubo *cualquier* error de filas → abortamos todo.
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Importación cancelada: hay errores en el archivo. Corrige y vuelve a intentar.",
                    "errors": errors,
                },
            )

        # 8) Auditoría única (resumen de importación) si el nivel lo amerita:
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            await log_action(
                db,
                action="IMPORT",
                entity="Purchase",
                description=f"Importación OK: {imported} compras. Stock recalculado en {len(pairs_to_recalc)} pares.",
                user_id=uid,
            )

        # 9) Confirmamos la transacción global (todas las filas correctas + auditoría + recalculo stock).
        await db.commit()

        # 10) Respuesta al cliente con métricas (sin errores porque TODO-O-NADA).
        return {
            "ok": True,
            "imported": imported,
            "recalculated_pairs": len(pairs_to_recalc),
            "errors": [],  # vacío por contrato TODO-O-NADA
        }

    # ------------------------------
    # MANEJO DE ERRORES GLOBALES (garantiza ROLLBACK)
    # ------------------------------
    except IntegrityError as e:
        # Violaciones de integridad (FK/UK) que se escapan del manejo por-fila.
        await db.rollback()
        logger.error("Error de integridad en importación: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={"message": "Importación cancelada por error de integridad.", "errors": [str(e.orig)]},
        )

    except HTTPException:
        # Repropagamos errores HTTP ya formados manteniendo el status code.
        await db.rollback()
        raise

    except Exception as e:
        # Cualquier otro error no previsto: garantizamos rollback y trazabilidad.
        await db.rollback()
        logger.exception("Error inesperado en importación", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"message": "Error interno en importación.", "errors": [str(e)]},
        )