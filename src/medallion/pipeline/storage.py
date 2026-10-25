"""Delta insert-only: snapshots completos e verificados, sem apagar histórico."""
import re
import json
from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import uuid4
from medallion.silver.transform import canonical, digest
from medallion.synthetic.contracts import CONTRACTS

DIM_EXTRA=['vigente_desde','vigente_ate','row_key','payload_json']
TX_EXTRA=['status_transacao','motivo_recusa','id_conta','id_cliente','nome','cidade','segmento','cliente_versao','conta_versao','cartao_versao','payload_json','row_key']
SILVER={f:list(fields)+(DIM_EXTRA if f.endswith('_cdc') else TX_EXTRA if f=='transacoes' else ['payload_json','row_key']) for f,fields in CONTRACTS.items()}
SILVER['quarentena']=['fonte','id_origem','motivo','payload_json','row_key']
GOLD={
'gold_fato_transacao':SILVER['transacoes']+['valor_bruto','valor_estornado','valor_liquido','data_corte','mes','id_estabelecimento'],
'gold_cliente_mes':['row_key','id_cliente','mes','tentativas','aprovadas','recusadas','canceladas','valor_bruto','valor_estornado','valor_liquido'],
'gold_indicadores_risco':['row_key','id_transacao','id_cliente','eventos','chargebacks','valor_estornado','data_corte'],
'gold_features_cliente':['row_key','id_cliente','data_corte','tentativas','aprovadas','recusadas','valor_liquido','dias_desde_ultima_compra'],
'gold_dim_cliente':SILVER['clientes_cdc'],'gold_dim_conta':SILVER['contas_cdc'],'gold_dim_cartao':SILVER['cartoes_cdc'],
'gold_dim_estabelecimento':['row_key','id_estabelecimento','estabelecimento']}


def tipo(k):
    if k in ('renda','limite','valor','valor_estorno','valor_bruto','valor_estornado','valor_liquido'):return 'DECIMAL(18,2)'
    if k in ('data_atualizacao','data_transacao','data_evento','data_estorno','vigente_desde','vigente_ate'):return 'TIMESTAMP'
    if k in ('data_abertura','mes','data_corte'):return 'DATE'
    if k in ('tentativas','aprovadas','recusadas','canceladas','eventos','chargebacks','dias_desde_ultima_compra'):return 'BIGINT'
    return 'STRING'


def validar_snapshot(snapshot):
    if not re.fullmatch('[a-f0-9]{64}',snapshot):raise ValueError('snapshot_id deve ser SHA256')
    return snapshot


def normalize(rows, fields):
    return [{k:r.get(k) for k in fields} for r in rows]


def fingerprint(rows):
    return digest(sorted((canonical(r) for r in rows)))


def merge(spark, table, rows, fields, snapshot):
    validar_snapshot(snapshot)
    fields=list(dict.fromkeys(fields))
    records=[{'snapshot_id':snapshot,**r} for r in normalize(rows,fields)]
    if len({r['row_key'] for r in records})!=len(records):raise ValueError('row_key duplicada')
    schema='snapshot_id STRING, '+', '.join(f'`{k}` {tipo(k)}' for k in fields)
    spark.sql(f'CREATE TABLE IF NOT EXISTS {table} ({schema}) USING DELTA')
    existing=[r.asDict() for r in spark.sql(f"SELECT * FROM {table} WHERE snapshot_id='{snapshot}'").collect()]
    bykey={r['row_key']:r for r in records}
    if len({r['row_key'] for r in existing})!=len(existing):raise ValueError('duplicidade persistida')
    for r in existing:
        if r['row_key'] not in bykey or canonical(r)!=canonical(bykey[r['row_key']]):raise ValueError('Conflito em snapshot existente')
    if records:
        view='_homol_'+uuid4().hex
        spark.createDataFrame(records,schema).createOrReplaceTempView(view)
        try:
            spark.sql(f'MERGE INTO {table} t USING {view} s ON t.snapshot_id=s.snapshot_id AND t.row_key=s.row_key WHEN NOT MATCHED THEN INSERT *')
        finally:spark.catalog.dropTempView(view)
    after=[r.asDict() for r in spark.sql(f"SELECT * FROM {table} WHERE snapshot_id='{snapshot}'").collect()]
    if fingerprint(after)!=fingerprint(records):raise ValueError('Releitura Delta divergente')
    return {'linhas':len(records),'inseridas':len(records)-len(existing),'hash':fingerprint(after)}


def table(config,layer,name):
    return config.tabela_sql('prata' if layer=='silver' else 'ouro', ('silver_'+name if layer=='silver' else name))


def read(spark,config,layer,snapshot):
    validar_snapshot(snapshot)
    marker=config.tabela_sql('controle','snapshots_homologacao')
    marks=spark.sql(f"SELECT * FROM {marker} WHERE snapshot_id='{snapshot}' AND camada='{layer}'").collect()
    if len(marks)!=1:
        raise ValueError('Snapshot sem conclusão ou camada incorreta')
    report=json.loads(marks[0]['relatorio_json'])
    fields=SILVER if layer=='silver' else GOLD
    result={}
    for name in fields:
        rows=[r.asDict() for r in spark.sql(f"SELECT * FROM {table(config,layer,name)} WHERE snapshot_id='{snapshot}'").collect()]
        if len(rows)!=report[name]['linhas'] or fingerprint(rows)!=report[name]['hash']:
            raise ValueError('Snapshot diverge do marcador: '+name)
        result[name]=[{k:(v.replace(tzinfo=timezone.utc) if isinstance(v,datetime) and v.tzinfo is None else v) for k,v in r.items() if k!='snapshot_id'} for r in rows]
    return result
