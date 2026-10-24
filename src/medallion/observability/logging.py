"""Logs JSON com contexto de execução, sem configurar o logger raiz."""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "nivel": record.levelname,
            "evento": record.getMessage(),
        }
        dados.update(getattr(record, "contexto", {}))
        if record.exc_info:
            dados["erro"] = self.formatException(record.exc_info)
        return json.dumps(dados, ensure_ascii=False)


def obter_logger() -> logging.Logger:
    logger = logging.getLogger("medallion")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
