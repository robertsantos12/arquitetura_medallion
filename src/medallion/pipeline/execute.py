"""Orquestração de homologação, sem alterações nos dados anteriores."""
import json
from datetime import date
from medallion.bronze.validate import validar_bronze
from medallion.silver.transform import transformar, digest, canonical, semantica
from medallion.gold.transform import construir
from medallion.pipeline.storage import SILVER,GOLD,merge,read,table,normalize,fingerprint
from medallion.observability.audit import AuditRun,capturar_fontes
from medallion.observability.audit_delta import DeltaAuditSink


def executar(spark,config,raiz,camada,snapshot_silver='',data_corte='2026-05-31'):
    if config.ambiente!='dev' or not config.data_referencia:raise ValueError('Homologação apenas dev com data_referencia')
    date.fromisoformat(data_corte)
    if camada not in ('silver','gold'):raise ValueError('Camada inválida')
    spark.conf.set('spark.sql.session.timeZone','UTC')
    sources=capturar_fontes(raiz)
    sink=DeltaAuditSink(spark,config);sink.preparar()
    run=AuditRun(sink.raiz,sink,config,'homologacao_'+camada,sources,{'spark':spark.version,'corte':data_corte,'snapshot_silver':snapshot_silver})
    result={}
    def process(ctx):
        if camada=='silver':
            origin,bronze=validar_bronze(spark,config)
            datasets=transformar(origin)
            input_hash=digest({f:sorted(canonical(r) for r in rs) for f,rs in origin.items()})
            ctx.verificar('bronze_reconciliada',sum(r['linhas_lidas'] for r in bronze.values()),sum(len(rs) for rs in origin.values()))
            for f in SILVER:
                if f=='quarentena':continue
                distinct=len(set(canonical(semantica(f,r)) for r in origin[f]))
                rejected=sum(r['fonte']==f for r in datasets['quarentena'])
                ctx.verificar('reconciliacao_'+f,len(datasets[f])+rejected,distinct)
        else:
            source=read(spark,config,'silver',snapshot_silver)
            datasets=construir(source,data_corte);input_hash=snapshot_silver
            ctx.verificar('financeiro_mensal',str(sum(r['valor_liquido'] for r in datasets['gold_cliente_mes'])),str(sum(r['valor_liquido'] for r in datasets['gold_fato_transacao'])))
        snapshot=digest([camada,input_hash,data_corte if camada=='gold' else '',digest(sources)])
        fields=SILVER if camada=='silver' else GOLD
        schema=config.schema_sql('prata' if camada=='silver' else 'ouro')
        spark.sql(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        report={}
        for name,cols in fields.items():
            report[name]=merge(spark,table(config,camada,name),datasets[name],cols,snapshot)
        ctx.verificar('tabelas_relidas',len(report),len(fields))
        # Repetição efetiva do MERGE: nenhum registro deve ser inserido.
        again=[merge(spark,table(config,camada,n),datasets[n],cols,snapshot)['inseridas'] for n,cols in fields.items()]
        ctx.verificar('repeticao_sem_insercoes',sum(again),0)
        marker=[dict(row_key=snapshot,camada=camada,relatorio_json=canonical({n:{k:v for k,v in x.items() if k!='inseridas'} for n,x in report.items()}))]
        merge(spark,config.tabela_sql('controle','snapshots_homologacao'),marker,['row_key','camada','relatorio_json'],snapshot)
        result.update(snapshot_id=snapshot,relatorio=report)
    run.executar(process)
    print(camada.upper()+' HOMOLOGAÇÃO: OK')
    print(json.dumps(result,ensure_ascii=False));print(sink.verificar(run.run_id))
    return result
