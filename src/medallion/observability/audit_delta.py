"""Adaptador Databricks: eventos Delta e arquivos em Unity Catalog Volume."""

from datetime import datetime
from uuid import UUID

from medallion.observability.audit import serializar, verificar_arquivos


class DeltaAuditSink:
    def __init__(self, spark, config):
        if config.ambiente != "dev":
            raise ValueError("Prova de rastreabilidade habilitada apenas para dev")
        self.spark = spark
        self.config = config
        self.tabela = config.tabela_sql("controle", "execucoes_eventos")
        self.volume = config.tabela_sql("controle", "evidencias")
        self.raiz = f"/Volumes/{config.catalogo}/{config.schema('controle')}/evidencias/execucoes"

    def preparar(self):
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema_sql('controle')}")
        self.spark.sql(f"CREATE VOLUME IF NOT EXISTS {self.volume}")
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {self.tabela} (
                event_id STRING, run_id STRING, batch_id STRING, etapa STRING,
                status STRING, timestamp_utc TIMESTAMP, payload_json STRING,
                arquivo STRING, arquivo_sha256 STRING
            ) USING DELTA
        """)

    def append(self, evento, arquivo, digest):
        schema = ("event_id STRING, run_id STRING, batch_id STRING, etapa STRING, "
                  "status STRING, timestamp_utc TIMESTAMP, payload_json STRING, "
                  "arquivo STRING, arquivo_sha256 STRING")
        linha = (evento["event_id"], evento["run_id"], evento["batch_id"],
                 evento["etapa"], evento["status"], datetime.fromisoformat(evento["timestamp_utc"]),
                 serializar(evento).decode(), arquivo, digest)
        self.spark.createDataFrame([linha], schema).write.format("delta").mode("append").saveAsTable(self.tabela)

    def verificar(self, run_id):
        run_id = str(UUID(run_id))
        rows = self.spark.sql(
            f"SELECT * FROM {self.tabela} WHERE run_id = '{run_id}' ORDER BY timestamp_utc, event_id"
        ).collect()
        return verificar_arquivos([r.asDict() for r in rows])
