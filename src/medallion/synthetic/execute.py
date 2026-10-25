"""Adaptador de execução Databricks; notebook fino e módulos testáveis."""

import json

from medallion.observability.audit import AuditRun, capturar_fontes, serializar, sha256
from medallion.observability.audit_delta import DeltaAuditSink
from medallion.synthetic.contracts import CONTRACTS
from medallion.synthetic.publish import conferir, publicar


def executar_geracao(spark, config, raiz_projeto):
    if config.ambiente != "dev" or config.modo != "incremental":
        raise ValueError("Geração sintética restrita a dev/incremental")
    if not config.data_referencia:
        raise ValueError("Geração exige data_referencia explícita")
    # Apenas Volume padrão deste catálogo; nenhum path arbitrário é criado.
    padrao = f"/Volumes/{config.catalogo}/{config.schema('landing')}/arquivos"
    if config.caminho_entrada != padrao:
        raise ValueError("Nesta etapa use o Volume de entrada padrão")
    sink = DeltaAuditSink(spark, config)
    sink.preparar()
    run = AuditRun(sink.raiz, sink, config, "geracao_sintetica", capturar_fontes(raiz_projeto),
                   {"spark": spark.version, "cenario": "v1"})
    resultado = {}

    def processar(ctx):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.schema_sql('landing')}")
        spark.sql(f"CREATE VOLUME IF NOT EXISTS {config.tabela_sql('landing', 'arquivos')}")
        resultado.update(publicar(config.caminho_entrada, config.data_referencia))
        actual = conferir(config.caminho_entrada, config.data_referencia)
        ctx.verificar("arquivos_relidos", actual, resultado["manifesto"]["arquivos"])
        ctx.verificar("seis_fontes", sorted({a["fonte"] for a in actual}), sorted(CONTRACTS))
        ctx.verificar("hash_manifesto", resultado["manifesto_sha256"], sha256(serializar(resultado["manifesto"])))
        repeticao = publicar(config.caminho_entrada, config.data_referencia)
        ctx.verificar("repeticao_sem_novas_gravacoes", repeticao["novos_arquivos"], 0)
        ctx.verificar("hash_manifesto_repeticao", repeticao["manifesto_sha256"], resultado["manifesto_sha256"])

    run.executar(processar)
    verificacao = sink.verificar(run.run_id)
    print("DADOS SINTÉTICOS: OK")
    print("Pasta do cenário:", resultado["pasta"])
    print("Manifesto SHA256:", resultado["manifesto_sha256"])
    print("Novos arquivos (inclui manifesto):", resultado["novos_arquivos"])
    print("Arquivos reutilizados:", resultado["reutilizados"])
    for lote in resultado["manifesto"]["ordem_chegada"]:
        resumo = {f: sum(a["registros"] for a in resultado["manifesto"]["arquivos"]
                         if a["lote"] == lote and a["fonte"] == f) for f in CONTRACTS}
        print(json.dumps({"lote": lote, "registros": resumo}, ensure_ascii=False))
    print("RUN_ID_GERACAO=" + run.run_id)
    print(verificacao)
    return {"run_id": run.run_id, **resultado, "verificacao": verificacao}
