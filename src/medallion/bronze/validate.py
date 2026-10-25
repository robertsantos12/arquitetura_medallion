"""Validador somente leitura do manifesto, linhas e controle Bronze V2."""
import json
from hashlib import sha256
from medallion.bronze.ingest_v2 import FONTES, LOTES, preparar_lote
from medallion.silver.transform import canonical


def validar_bronze(spark,config):
    expected={f:{} for f in FONTES}; files=[]
    for lote in LOTES:
        dados,_=preparar_lote(config.caminho_entrada,config.data_referencia,lote)
        for item,rows in dados:
            files.append(item)
            for i,row in enumerate(rows,1):
                id_=sha256(f"v2|{config.data_referencia}|{item['caminho']}|{i}".encode()).hexdigest()
                expected[item['fonte']][id_]=(item['caminho'],item['sha256'],i,canonical(row))
    result={};origin={}
    for f in FONTES:
        rows=spark.sql(f"SELECT * FROM {config.tabela_sql('bronze','raw_'+f)} WHERE data_referencia='{config.data_referencia}' LIMIT 100001").collect()
        if len(rows)>100000:raise ValueError('Limite de homologação excedido; usar implementação distribuída')
        if len({r['id_registro'] for r in rows})!=len(rows):raise ValueError('id_registro duplicado')
        actual={r['id_registro']:(r['arquivo'],r['arquivo_sha256'],r['linha'],canonical(json.loads(r['payload_json']))) for r in rows}
        if actual!=expected[f]:raise ValueError('Bronze diverge do manifesto/payload: '+f)
        origin[f]=[json.loads(r['payload_json']) for r in rows]
        result[f]={'linhas_lidas':len(rows),'inseridas':0,'existentes':len(rows),'arquivos':sum(i['fonte']==f for i in files)}
    control=spark.sql(f"SELECT * FROM {config.tabela_sql('controle','arquivos_bronze_v2')} WHERE cenario='v2' AND data_referencia='{config.data_referencia}'").collect()
    actual={(r['arquivo'],r['arquivo_sha256'],r['registros']) for r in control}
    wanted={(i['caminho'],i['sha256'],i['registros']) for i in files}
    if actual!=wanted or len(control)!=len(wanted):raise ValueError('Controle de arquivos divergente ou duplicado')
    return origin,result
