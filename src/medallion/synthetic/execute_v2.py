"""Execução auditada da massa V2 no workspace Databricks."""
import json
from medallion.observability.audit import AuditRun, capturar_fontes, serializar, sha256
from medallion.observability.audit_delta import DeltaAuditSink
from medallion.synthetic.contracts import CONTRACTS
from medallion.synthetic.publish_v2 import conferir_v2, publicar_v2

def executar_geracao_v2(spark, config, raiz_projeto):
    if config.ambiente!="dev" or config.modo!="incremental" or not config.data_referencia:
        raise ValueError("V2 exige dev, incremental e data_referencia")
    padrao=f"/Volumes/{config.catalogo}/{config.schema('landing')}/arquivos"
    if config.caminho_entrada!=padrao:
        raise ValueError("Use o Volume de entrada padrão")
    sink=DeltaAuditSink(spark,config)
    sink.preparar()
    run=AuditRun(sink.raiz,sink,config,"geracao_sintetica_v2",capturar_fontes(raiz_projeto),
                 {"spark":spark.version,"cenario":"v2"})
    resultado={}
    def processar(ctx):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.schema_sql('landing')}")
        spark.sql(f"CREATE VOLUME IF NOT EXISTS {config.tabela_sql('landing','arquivos')}")
        resultado.update(publicar_v2(config.caminho_entrada,config.data_referencia))
        atual=conferir_v2(config.caminho_entrada,config.data_referencia)
        ctx.verificar("arquivos_relidos_v2",atual,resultado["manifesto"]["arquivos"])
        ctx.verificar("seis_fontes_v2",sorted({a["fonte"] for a in atual}),sorted(CONTRACTS))
        ctx.verificar("hash_manifesto_v2",resultado["manifesto_sha256"],sha256(serializar(resultado["manifesto"])))
        repeticao=publicar_v2(config.caminho_entrada,config.data_referencia)
        ctx.verificar("repeticao_v2",repeticao["novos_arquivos"],0)
        ctx.verificar("hash_repeticao_v2",repeticao["manifesto_sha256"],resultado["manifesto_sha256"])
    run.executar(processar)
    verificacao=sink.verificar(run.run_id)
    print("DADOS SINTÉTICOS V2: OK")
    print("Pasta do cenário:",resultado["pasta"])
    print("Manifesto SHA256:",resultado["manifesto_sha256"])
    print("Arquivos novos:",resultado["novos_arquivos"])
    for lote in resultado["manifesto"]["ordem_chegada"]:
        resumo={f:sum(a["registros"] for a in resultado["manifesto"]["arquivos"] if a["lote"]==lote and a["fonte"]==f) for f in CONTRACTS}
        print(json.dumps({"lote":lote,"registros":resumo},ensure_ascii=False))
    print("RUN_ID_GERACAO_V2="+run.run_id)
    print(verificacao)
    return {"run_id":run.run_id,**resultado,"verificacao":verificacao}
