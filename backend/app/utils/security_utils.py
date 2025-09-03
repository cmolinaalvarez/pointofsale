import re
import html
from fastapi import HTTPException, status
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityUtils:
    # Patrones de inyección SQL
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)",
        r"(\-\-|\#|\/\*)",
        r"(\b(OR|AND)\s+['\"]?[01]['\"]?\s*[=<>])",
        r"(;|\|&)",
    ]
    
    # Patrones de XSS
    XSS_PATTERNS = [
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"vbscript:",
        r"expression\s*\(",
    ]
    
    # Campos sensibles que deben ser ofuscados en logs
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'credit_card', 
        'cvv', 'expiration_date', 'ssn', 'phone_number', 'email'
    }

    @classmethod
    def sanitize_input(cls, input_string: str, field_name: str = None) -> str:
        """
        Sanitiza y valida una entrada de texto
        """
        if not isinstance(input_string, str):
            return input_string
            
        # 1. Validar longitud máxima
        if field_name and hasattr(cls, 'FIELD_MAX_LENGTHS'):
            max_length = cls.FIELD_MAX_LENGTHS.get(field_name, 255)
            if len(input_string) > max_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name} excede la longitud máxima permitida"
                )
        
        # 2. Filtrar inyección SQL
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(f"Intento de inyección SQL detectado en campo {field_name}: {input_string}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entrada contiene patrones potencialmente peligrosos"
                )
        
        # 3. Sanitizar XSS
        cleaned = input_string
        for pattern in cls.XSS_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # 4. Escapar caracteres HTML
        cleaned = html.escape(cleaned)
        
        return cleaned

    @classmethod
    def sanitize_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza todos los campos de un diccionario
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_input(value, key)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_data(item) if isinstance(item, dict) else 
                                 cls.sanitize_input(item, key) if isinstance(item, str) else item 
                                 for item in value]
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def obfuscate_sensitive_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ofusca datos sensibles para logging
        """
        obfuscated = data.copy()
        for key in obfuscated.keys():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_FIELDS):
                obfuscated[key] = "***REDACTED***"
        return obfuscated

# Configuración de longitudes máximas por tipo de campo
SecurityUtils.FIELD_MAX_LENGTHS = {
    'code': 10,
    'name': 100,
    'description': 500,
    'basis': 20,
    'email': 254,
    'username': 50,
    'password': 128,
}