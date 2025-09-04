import logging, logging.config, os, sys, json
from app.core.config import settings

class JsonFormatter(logging.Formatter):
    def format(self, r: logging.LogRecord) -> str:
        payload = {"level": r.levelname, "logger": r.name, "msg": r.getMessage()}
        for k in ("user_id","ip","path","method"): 
            if hasattr(r,k): payload[k] = getattr(r,k)
        return json.dumps(payload, ensure_ascii=False)

def setup_logging() -> None:
    if settings.APP_ENV == "production":
        fmt = {"()": JsonFormatter}
        handlers = {"stdout":{"class":"logging.StreamHandler","stream":"ext://sys.stdout","formatter":"json","level":"INFO"}}
        root = {"level":"INFO","handlers":["stdout"]}
    else:
        fmt = {"console":{"format":"%(levelname)s | %(name)s | %(message)s"}}
        handlers = {"console":{"class":"logging.StreamHandler","stream":"ext://sys.stdout","formatter":"console","level":"DEBUG"}}
        root = {"level":"INFO","handlers":["console"]}
    logging.config.dictConfig({
        "version":1,"disable_existing_loggers":False,
        "formatters":fmt,"handlers":handlers,"root":root,
        "loggers":{"security":{"level":"INFO","handlers":root["handlers"],"propagate":False},
                   "uvicorn.access":{"level":"WARNING"},
                   "uvicorn.error":{"level":"INFO"},
                   "sqlalchemy.engine.Engine":{"level":"WARNING"}}
    })