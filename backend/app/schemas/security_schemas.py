from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from app.utils.security_utils import SecurityUtils

class SecureBaseModel(BaseModel):
    """
    Modelo base Pydantic con validaciones de seguridad integradas
    """
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_all_fields(cls, value: Any, info):
        """Validador que aplica sanitización a todos los campos string"""
        field_name = info.field_name
        
        if isinstance(value, str):
            return SecurityUtils.sanitize_input(value, field_name)
        
        # Para diccionarios y listas, aplicar sanitización recursiva
        if isinstance(value, dict):
            return SecurityUtils.sanitize_data(value)
        elif isinstance(value, list):
            return [SecurityUtils.sanitize_data(item) if isinstance(item, dict) else 
                    SecurityUtils.sanitize_input(item, field_name) if isinstance(item, str) else item 
                    for item in value]
        
        return value

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True