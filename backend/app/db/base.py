# Importa `DeclarativeBase` desde SQLAlchemy ORM
# Esta clase se usa para definir una base común para todos los modelos de la base de datos
from sqlalchemy.orm import DeclarativeBase

# Se define una clase llamada `Base` que hereda de `DeclarativeBase`
# Esta clase será la "base" de todos los modelos de la base de datos en tu aplicación
# Es decir, cada tabla (modelo) que crees en SQLAlchemy heredará de esta clase
class Base(DeclarativeBase):
    """Base para todos los modelos ORM"""
    pass  # No necesita ningún contenido adicional; hereda todo lo necesario de DeclarativeBase
