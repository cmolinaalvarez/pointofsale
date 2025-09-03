from sqlalchemy.future import select
from uuid import UUID
from app.models.account import Account, AccountTypeEnum  # ✅ Importar el enum
from app.schemas.account import AccountCreate, AccountUpdate, AccountPatch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi import HTTPException
from app.utils.audit import log_action
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from sqlalchemy import func
from typing import Optional
from app.utils.audit_level import get_audit_level

logger = logging.getLogger(__name__)

async def create_account(db: AsyncSession, account_in: AccountCreate, user_id: UUID):
    try:
        account = Account(**account_in.model_dump(), user_id=user_id)
        db.add(account)
        await db.flush()
        
        log = None
        description = f"Cuenta creada: {account.name} (id={account.id}, code={account.code})"
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            log = await log_action(
                db, 
                action="CREATE", 
                entity="Account", 
                entity_id=account.id,
                description=description,
                user_id=user_id
            )
            
        return account, log
        
    except Exception as e:
        logger.exception("Error al crear el accounto")
        raise

async def get_accounts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    try:
        query = select(Account)
        if search:
            query = query.where(Account.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Account.active == active)

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        result = await db.execute(query.offset(skip).limit(limit).order_by(Account.name))
        accounts = result.scalars().all()
        
        # ✅ Devolver el enum completo
        account_type_enum = {item.name: item.value for item in AccountTypeEnum}
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db, action="GETALL", entity="Account",
                description=f"Consulta de cuentas - search='{search}', active={active}",
                user_id=user_id
            )

        return {
            "total": total, 
            "items": accounts,
            "account_type_enum": account_type_enum  # ✅ Enum incluido
        }
        
    except Exception as e:
        await db.rollback()
        logger.exception("Error en get_accounts")
        raise

  
async def get_account_by_id(
    db: AsyncSession,
    account_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Account:
    """
    Recupera una cuenta por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        account_id (UUID): ID de la cuenta a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Account: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la cuenta.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalars().first()

        if not account:
            logger.warning(f"[GET_BRAND_BY_ID] Cuenta no encontrada: {account_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuanta con ID {account_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Account",
                    entity_id=account.id,
                    description=f"Consultó la cuenta: {account.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return account

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar el accounto {account_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la cuenta"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar la cuenta {account_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la cuenta"
        )       


# UPDATE (PUT = total)
async def update_account(
    db: AsyncSession,
    account_id: UUID,
    account_in: 'AccountUpdate',
    user_id: UUID
):
    """
    Actualiza una cuenta y construye el log de auditoría.
    - Retorna (account_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (account, None)
    - Si el accounto no existe, retorna (None, None)
    """
    try:
        # 1. Busca la categoría existente
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalars().first()
        if not account:
            logger.info(f"[update_account] Accounto {account_id} no encontrado.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if account.code != account_in.code:
            cambios.append(f"código: '{account.code}' → '{account_in.code}'")
            account.code = account_in.code

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if account.name != account_in.name:
            existing = await db.execute(
                select(Account).where(Account.name == account_in.name, Account.id != account_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_account] Nombre duplicado: {account_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe el accounto con el nombre '{account_in.name}'."
                )
            cambios.append(f"nombre: '{account.name}' → '{account_in.name}'")
            account.name = account_in.name

        # 3. Detecta y aplica otros cambios
        if account.code != account_in.code:
            cambios.append(f"code: '{account.code}' → '{account_in.code}'")
            account.code = account_in.code
        
            # 3. Detecta y aplica otros cambios
        if account.description != account_in.description:
            cambios.append(f"code: '{account.description}' → '{account_in.description}'")
            account.description = account_in.description
        
        if account.active != account_in.active:
            cambios.append(f"activo: {account.active} → {account_in.active}")
            account.active = account_in.active

        # 4. Si no hay cambios, retorna solo la categoría (sin log)
        if not cambios:
            logger.info(f"[update_account] No hubo cambios en el accounto {account_id}.")
            return account, None

        # 5. Actualiza el timestamp
        account.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Account",
                entity_id=account.id,
                description=f"Cambios en la Accounto: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_account] Accounto {account_id} actualizado por usuario {user_id}.")
        return account, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_account] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_account] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_account] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_account(
    db: AsyncSession,
    account_id: UUID,
    account_in: 'AccountPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente un accounto (PATCH) y registra log de auditoría.
    Retorna (account_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la cuenta existente
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalars().first()
        if not account:
            logger.warning(f"[patch_account] Marca {account_id} no encontrada.")
            return None, None

        data = account_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(account, field):
                old_value = getattr(account, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(account, field, value)

        if not cambios:
            logger.info(f"[patch_account] No hubo cambios en el accounto {account_id}.")
            return account, None

        account.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Account",
                entity_id=account.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_account] Cuenta {account_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return account, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_account] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_account] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_account] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )