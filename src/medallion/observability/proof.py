"""Prova pequena de persistência real, sem criar dados de negócio."""

import json

from medallion.observability.audit import AuditRun, capturar_fontes
from medallion.observability.audit_delta import DeltaAuditSink


def executar_prova(spark, config, raiz_projeto):
    sink = DeltaAuditSink(spark, config)
    sink.preparar()
    fontes = capturar_fontes(raiz_projeto)
    runtime = {"spark": spark.version, "tipo_teste": "prova_controlada"}
    ids = []
    for _ in range(2):
        run = AuditRun(sink.raiz, sink, config, "prova_sucesso", fontes, runtime)

        def validar(ctx):
            valor = spark.sql("SELECT CAST(2 + 2 AS BIGINT) AS valor").first()["valor"]
            ctx.verificar("consulta_spark", valor, 4)

        run.executar(validar)
        ids.append(run.run_id)
    falha = AuditRun(sink.raiz, sink, config, "prova_falha_controlada", fontes, runtime)
    try:
        falha.executar(lambda ctx: ctx.verificar("erro_controlado", 1, 2))
    except AssertionError:
        # Apenas a falha deliberada do teste é esperada. Falhas de I/O propagam.
        pass
    else:
        raise AssertionError("A falha controlada deveria interromper a tentativa")
    ids.append(falha.run_id)
    if len(set(ids)) != 3:
        raise AssertionError("Retentativas devem ter run_id distintos")
    relatorio = [sink.verificar(run_id) for run_id in ids]
    if [r["status"] for r in relatorio] != ["SUCESSO", "SUCESSO", "FALHOU"]:
        raise AssertionError("Estados persistidos inesperados")
    print("RASTREABILIDADE: OK")
    print("Falha controlada esperada: registrada e verificada")
    print("Tabela:", sink.tabela)
    print("Volume:", sink.raiz)
    print("RUN_IDS_PARA_RELEITURA=" + json.dumps(ids))
    return relatorio
