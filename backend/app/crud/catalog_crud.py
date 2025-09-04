# app/crud/catalog_crud.py
from __future__ import annotations
from typing import Any, Iterable, Optional, Sequence
from uuid import UUID
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.security_utils import SecurityUtils
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level

logger = logging.getLogger(__name__)

class CatalogCRUD:
    """
    CRUD seguro y consistente para catálogos con campos típicos:
    code/name/description/active (+extras). Replica el patrón de PaymentTerm.
    """
    def __init__(
        self,
        model,
        table_name: str,
        unique_fields: Sequence[str] = ("code",),
        search_fields: Sequence[str] = ("name", "code"),
        order_field: Optional[str] = "name",
        active_field: Optional[str] = "active",
    ):
        self.model = model
        self.table_name = table_name
        self.unique_fields = tuple(unique_fields)
        self.search_fields = tuple(search_fields)
        self.order_field = order_field
        self.active_field = active_field

    # ---------- helpers ----------
    def _get_col(self, name: str):
        return getattr(self.model, name)

    def _apply_search(self, query, search: Optional[str]):
        if not search:
            return query
        s = SecurityUtils.sanitize_input(search, "search")
        conds = []
        for f in self.search_fields:
            if hasattr(self.model, f):
                conds.append(self._get_col(f).ilike(f"%{s}%"))
        return query.where(func.bool_or(*conds) if len(conds) > 1 else conds[0]) if conds else query

    def _apply_active(self, query, active: Optional[bool]):
        if active is None or not self.active_field or not hasattr(self.model, self.active_field):
            return query
        return query.where(self._get_col(self.active_field) == active)

    async def _check_uniques(self, db: AsyncSession, data: dict, exclude_id: Optional[UUID] = None):
        for f in self.unique_fields:
            if f not in data or not hasattr(self.model, f):
                continue
            stmt = select(self.model).where(self._get_col(f) == data[f])
            if exclude_id is not None:
                stmt = stmt.where(self._get_col("id") != exclude_id)
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{self.model.__name__} con {f} '{data[f]}' ya existe",
                )

    # ---------- ops ----------
    async def create(self, db: AsyncSession, payload: dict, user_id: UUID):
        try:
            data = SecurityUtils.sanitize_data(payload)
            await self._check_uniques(db, data)
            obj = self.model(**data)
            if hasattr(obj, "user_id"):
                obj.user_id = user_id
            db.add(obj)
            await db.flush()

            audit_level = await get_audit_level(db)
            if audit_level and audit_level >= 2:
                await log_action(db, "CREATE", self.table_name, obj.id, user_id, {}, data)
            return obj

        except HTTPException:
            await db.rollback()
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error("Integridad al crear %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=400, detail="Violación de integridad")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB crear %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error crear %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def list(self, db: AsyncSession, skip=0, limit=100, search: Optional[str]=None, active: Optional[bool]=None, user_id: Optional[UUID]=None) -> dict:
        try:
            stmt = select(self.model)
            stmt = self._apply_search(stmt, search)
            stmt = self._apply_active(stmt, active)

            # total
            total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

            # order + page
            if self.order_field and hasattr(self.model, self.order_field):
                stmt = stmt.order_by(self._get_col(self.order_field))
            rows = (await db.execute(stmt.offset(skip).limit(limit))).scalars().all()

            audit_level = await get_audit_level(db)
            if audit_level and audit_level > 2 and user_id and hasattr(self.model, "id"):
                await log_action(db, "LIST", self.table_name, None, user_id, {}, {"skip": skip, "limit": limit, "search": search, "active": active})

            return {"total": total, "items": rows}

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB listar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Ocurrió un error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error listar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def get_by_id(self, db: AsyncSession, obj_id: UUID):
        try:
            res = await db.execute(select(self.model).where(self._get_col("id") == obj_id))
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail=f"{self.model.__name__} no encontrado")
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB obtener %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error obtener %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def update(self, db: AsyncSession, obj_id: UUID, payload: dict, user_id: UUID):
        try:
            res = await db.execute(select(self.model).where(self._get_col("id") == obj_id))
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail=f"{self.model.__name__} no encontrado")

            data = SecurityUtils.sanitize_data(payload)
            await self._check_uniques(db, data, exclude_id=obj_id)

            old = {}
            for k, v in data.items():
                if hasattr(obj, k):
                    old[k] = getattr(obj, k)
                    setattr(obj, k, v)

            if hasattr(obj, "updated_at"):
                from datetime import datetime as _dt
                obj.updated_at = _dt.utcnow()

            await db.flush()

            audit_level = await get_audit_level(db)
            if audit_level and audit_level >= 2:
                await log_action(db, "UPDATE", self.table_name, obj.id, user_id, old, data)

            return obj

        except HTTPException:
            await db.rollback()
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error("Integridad al actualizar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=400, detail="Violación de integridad")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB actualizar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error actualizar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def patch(self, db: AsyncSession, obj_id: UUID, patch: dict, user_id: UUID):
        try:
            res = await db.execute(select(self.model).where(self._get_col("id") == obj_id))
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail=f"{self.model.__name__} no encontrado")

            data = SecurityUtils.sanitize_data({k: v for k, v in patch.items() if v is not None})
            await self._check_uniques(db, data, exclude_id=obj_id)

            old = {}
            for k, v in data.items():
                if hasattr(obj, k):
                    old[k] = getattr(obj, k)
                    setattr(obj, k, v)

            if hasattr(obj, "updated_at"):
                from datetime import datetime as _dt
                obj.updated_at = _dt.utcnow()

            await db.flush()

            audit_level = await get_audit_level(db)
            if audit_level and audit_level >= 2:
                await log_action(db, "PATCH", self.table_name, obj.id, user_id, old, data)

            return obj

        except HTTPException:
            await db.rollback()
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error("Integridad al parchar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=400, detail="Violación de integridad")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB patch %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error patch %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def delete(self, db: AsyncSession, obj_id: UUID, user_id: UUID):
        try:
            res = await db.execute(select(self.model).where(self._get_col("id") == obj_id))
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail=f"{self.model.__name__} no encontrado")

            await db.delete(obj)

            audit_level = await get_audit_level(db)
            if audit_level and audit_level >= 2:
                await log_action(db, "DELETE", self.table_name, obj.id, user_id, {}, {})

            return True

        except HTTPException:
            await db.rollback()
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("DB eliminar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail="Error en la base de datos")
        except Exception as e:
            await db.rollback()
            logger.exception("Error eliminar %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    async def import_csv_text(self, db: AsyncSession, csv_text: str, user_id: UUID) -> dict:
        """
        Importa CSV con columnas: code, name, [description], [active].
        """
        import csv, io
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            imported, errors = [], []
            for idx, row in enumerate(reader, start=1):
                try:
                    data = {k: row.get(k) for k in ("code", "name", "description", "active")}
                    if isinstance(data.get("active"), str):
                        v = data["active"].strip().lower()
                        data["active"] = True if v in ("1", "true", "t", "yes", "y", "si", "sí") else False if v in ("0", "false", "f", "no", "n") else True
                    # upsert simple por code
                    if "code" in data and data["code"]:
                        exists = await db.execute(select(self.model).where(self._get_col("code") == data["code"]))
                        obj = exists.scalar_one_or_none()
                        if obj:
                            await self.patch(db, obj.id, data, user_id)
                        else:
                            await self.create(db, data, user_id)
                        imported.append(data["code"])
                    else:
                        raise ValueError("Fila sin 'code'")
                except Exception as e:
                    errors.append({"row": idx, "error": str(e), "row_data": row})

            return {"total_imported": len(imported), "total_errors": len(errors), "imported": imported, "errors": errors}

        except Exception as e:
            await db.rollback()
            logger.exception("Error import CSV %s: %s", self.table_name, e, exc_info=True)
            raise HTTPException(status_code=400, detail=f"Error importando CSV: {str(e)}")
