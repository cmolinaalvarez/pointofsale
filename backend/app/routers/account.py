from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional, Dict
from pydantic import BaseModel  # ✅ Importar BaseModel

from app.schemas.account import AccountCreate, AccountUpdate, AccountRead, AccountPatch
from app.crud.account import create_account, get_accounts, get_account_by_id, update_account, patch_account
from app.models.user import User
from app.dependencies.current_user import get_current_user
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Accounts"])

# ✅ Schema de respuesta para GET ALL
class AccountListResponse(BaseModel):
    total: int
    items: List[AccountRead]
    account_type_enum: Dict[str, str]

    class Config:
        from_attributes = True

# ✅ Schema de respuesta para GET BY ID
class AccountWithEnumResponse(BaseModel):
    account: AccountRead
    account_type_enum: Dict[str, str]

    class Config:
        from_attributes = True

@router.post("/", response_model=AccountRead)
async def create_account_endpoint(account_in: AccountCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    try:
        new_account, log = await create_account(db, account_in, current_user.id)
        if log:
            db.add(log)
        await db.commit()
        logger.info(f"Accounto creado: {new_account.id} por usuario {current_user.id}")
        return AccountRead.model_validate(new_account)
    except Exception as e:
        await db.rollback()
        logger.exception("Error al crear accounto")
        raise HTTPException(status_code=500, detail="Error interno")

@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await get_accounts(db, skip, limit, search, active, current_user.id)
        await db.commit()
        return result
    except Exception as e:
        await db.rollback()
        logger.exception("Error al listar accountos")
        raise HTTPException(status_code=500, detail="Error al obtener accountos")

@router.get("/{account_id}", response_model=AccountWithEnumResponse)
async def read_account(account_id: UUID, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    try:
        account = await get_account_by_id(db, account_id, current_user.id)
        
        # ✅ Obtener el enum para la respuesta individual
        from app.models.account import AccountTypeEnum
        account_type_enum = {item.name: item.value for item in AccountTypeEnum}
        
        await db.commit()
        return {
            "account": AccountRead.model_validate(account),
            "account_type_enum": account_type_enum
        }
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error al obtener accounto")
        raise HTTPException(status_code=500, detail="Error al consultar accounto")

# ==============================
# GET BY ID
# ==============================
@router.get("/{account_id}", response_model=AccountRead)
async def read_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        account = await get_account_by_id(db, account_id, current_user.id)
        await db.commit()   # Registrar la auditoría si la hubo
        return AccountRead.model_validate(account)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener el accounto: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener el accounto por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar el accounto"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{account_id}", response_model=AccountRead)
async def update_account_endpoint(
    account_id: UUID,
    account_in: AccountUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await update_account(db, account_id, account_in, current_user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Accounto no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return AccountRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el accounto: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el accounto", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{account_id}", response_model=AccountRead)
async def patch_account_endpoint(
    account_id: UUID,
    account_in: AccountPatch,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await patch_account(db, account_id, account_in, current_user.id)
        if not updated:
            logger.warning(f"[patch_account_endpoint] Accounto {account_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Accounto no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_account_endpoint] Accounto {account_id} actualizada parcialmente correctamente.")
        return AccountRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el accounto (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_account_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el accounto (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_accounts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info(f"Headers después de limpieza: {csv_reader.fieldnames}")
        accounts = []
        user_id = current_user.id
        count = 0
        for row in csv_reader:
            try:
                account = Account(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    debit=row["debit"],
                    debit_account_id=row["debit_account_id"],
                    credit=row["credit"],
                    credit_account_id=row["credit_account_id"],                    
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=current_user.id
                )
                accounts.append(account)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de accountos (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not accounts:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(accounts)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Account",
                description=f"Importación masiva: {len(accounts)} accountos importados.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de accountos exitosa. Total importadas: %d", len(accounts))
        return {"ok": True, "imported": len(accounts)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (accounto duplicada): {str(e.orig)}"
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en importación masiva: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en importación masiva", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )