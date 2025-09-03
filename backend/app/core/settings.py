from sqlalchemy.orm import Session
from app.models.setting import Setting

async def get_setting_async(db: Session, key: str, default=None):
    """
    Recupera el valor de una configuración (setting) desde la base de datos,
    realizando la conversión automática al tipo de dato correspondiente.
    Si no existe la configuración, retorna el valor por defecto.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        key (str): Llave (nombre) del setting a buscar.
        default (Any, opcional): Valor a retornar si el setting no existe.

    Returns:
        Any: Valor del setting (ya convertido al tipo correspondiente), o default.
    """

    # Busca el registro en la tabla 'settings' por la llave proporcionada
    setting = await db.query(Setting).filter_by(key=key).first()
    #print("SETTING:", setting.value)  
    
    # Si no existe el registro, retorna el valor por defecto
    if not setting:
        return default

    # Procesa según el tipo declarado en el setting
    if setting.type == "bool":
        # Interpreta el valor como booleano (acepta "true", "True", "TRUE")
        return setting.value.lower() == "true"
    if setting.type == "int":
        try:
            # Convierte a entero, si falla retorna default
            return int(setting.value)
        except Exception:
            return default

    # Para otros tipos (ej: "string", "float", etc), retorna el valor tal cual está en la BD
    return setting.value

# Si quieres, puedes agregar también set_setting o utilidades similares aquí.
