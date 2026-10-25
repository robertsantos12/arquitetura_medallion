"""Preparação idempotente dos namespaces de desenvolvimento."""

from medallion.config import PipelineConfig
from medallion.config.settings import CAMADAS
from medallion.observability.logging import obter_logger


def preparar_ambiente(spark, config: PipelineConfig) -> list[str]:
    """Cria schemas dev; deixa tabelas, volumes e dados para as próximas etapas.

    Uma falha mantém schemas já criados. A repetição é segura por usar
    IF NOT EXISTS. O bootstrap de hml/prod requer desenho de permissões futuro.
    """
    if config.ambiente != "dev":
        raise ValueError("Este bootstrap está habilitado apenas para dev")
    logger = obter_logger()
    contexto = {"batch_id": config.batch_id, "ambiente": config.ambiente}
    criados = []
    logger.info("bootstrap_iniciado", extra={"contexto": contexto})
    try:
        for camada in CAMADAS:
            schema = config.schema_sql(camada)
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            spark.sql(f"DESCRIBE SCHEMA {schema}").collect()
            criados.append(schema)
            logger.info("schema_disponivel", extra={"contexto": {**contexto, "schema": schema}})
    except Exception:
        logger.exception("bootstrap_falhou", extra={"contexto": contexto})
        raise
    logger.info("bootstrap_concluido", extra={"contexto": contexto})
    return criados
