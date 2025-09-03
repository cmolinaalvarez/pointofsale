# app/schemas/common.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class StrictModel(BaseModel):
    # Pydantic v2: usa model_config con ConfigDict
    model_config = ConfigDict(
        extra='forbid',              # rechaza campos desconocidos
        str_strip_whitespace=True,   # recorta espacios en strings
        validate_default=True,       # valida valores por defecto
        use_enum_values=True,        # serializa enums por valor
        arbitrary_types_allowed=False
    )

class WithCode(BaseModel):
    code: str = Field(..., min_length=1, max_length=32, pattern=r'^[A-Za-z0-9._-]+$')

class WithName(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class WithDescription(BaseModel):
    description: Optional[str] = Field(default=None, max_length=500)

class WithActive(BaseModel):
    active: bool = True
