from fastapi import Query
from pydantic import BaseModel, field_validator

class PageQuery(BaseModel):
    skip: int = Query(0, ge=0)
    limit: int = Query(100, ge=1, le=1000)
    search: str | None = Query(None, min_length=1, max_length=100)
    active: bool | None = None

    @field_validator("search")
    @classmethod
    def v_search(cls, v):
        if v:
            v = v.strip()
            # Evita comodines abusivos y patrones raros
            if any(t in v for t in ["--", ";", "/*", "*/"]):
                raise ValueError("search contiene patrones inválidos")
        return v