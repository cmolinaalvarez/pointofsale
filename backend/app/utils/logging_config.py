import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Limpia los handlers previos para evitar duplicados
    root_logger = logging.getLogger()
    while root_logger.handlers:
        handler = root_logger.handlers[0]
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        when="midnight",
        backupCount=14,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Asigna tus handlers como únicos
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Opcional: silencia logs ruidosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.INFO)