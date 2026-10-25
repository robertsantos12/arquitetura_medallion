"""Contrato aditivo Bronze por views, sem reescrever registros legados."""
import re
from medallion.bronze.validate import validar_bronze
from medallion.bronze.ingest_v2 import FONTES,carregar_manifesto


def select_contrato(config,fonte,version):
    if fonte not in FONTES or type(version) is not int or version<1:raise ValueError('Fonte/versão inválida')
    # PipelineConfig já valida catálogo e data. Path é o padrão explicitamente validado.
    prefix=f'/Volumes/{config.catalogo}/{config.schema("landing")}/arquivos/cenarios/v2/'
    return f"""SELECT b.*,
 concat('{prefix}',b.data_referencia,'/',b.arquivo) AS arquivo_origem,
 CAST(b.ingerido_em AS DATE) AS data_ingestao,
 b.ingerido_em AS timestamp_ingestao,
 sha2(concat('v2|',b.data_referencia,'|',b.lote),256) AS batch_id,
 'DERIVADO_CENARIO_DATA_LOTE_LEGADO' AS batch_id_origem,
 sha2(b.payload_json,256) AS hash_linha,
 CAST({version} AS INT) AS schema_version
 FROM {config.tabela_sql('bronze','raw_'+fonte)} b
 WHERE b.data_referencia='{config.data_referencia}'"""


def normalizar_sql(sql):
    return re.sub(r'\s+',' ',sql.strip().rstrip(';'))


def executar(spark,config):
    if config.ambiente!='dev' or not config.data_referencia:raise ValueError('Apenas dev com data_referencia')
    if config.raiz_arquivos is not None:raise ValueError('Use o Volume padrão desta etapa')
    spark.conf.set('spark.sql.session.timeZone','UTC')
    _,bronze=validar_bronze(spark,config)
    _,manifest,_=carregar_manifesto(config.caminho_entrada,config.data_referencia)
    version=manifest['schema_version']
    plans=[]
    # Views fixas para a data de referência homologada; não repontar existentes.
    for fonte in FONTES:
        name='raw_'+fonte+'_contrato_v2'
        full=config.tabela_sql('bronze',name)
        sql=select_contrato(config,fonte,version)
        old=spark.sql(f"SELECT view_definition FROM `{config.catalogo}`.information_schema.views WHERE table_schema='{config.schema('bronze')}' AND table_name='{name}'").collect()
        exists=spark.catalog.tableExists(full)
        if exists and (len(old)!=1 or old[0]['view_definition'] is None or normalizar_sql(old[0]['view_definition'])!=normalizar_sql(sql)):
            raise ValueError('Objeto existente incompatível; não será substituído: '+name)
        plans.append((fonte,name,full,sql,exists))
    report={}
    for fonte,name,full,sql,exists in plans:
        if not exists:
            spark.sql(f"CREATE VIEW {full} COMMENT 'Contrato Bronze V2 aditivo. batch_id derivado do lote legado, não recuperado da configuração original. Leitura UTC. Fonte física preservada.' AS {sql}")
        rows=spark.sql(f'SELECT * FROM {full}').collect()
        if len(rows)!=bronze[fonte]['linhas_lidas']:raise ValueError('Contagem divergente da Bronze: '+fonte)
        from hashlib import sha256
        for r in rows:
            batch=sha256(f"v2|{r['data_referencia']}|{r['lote']}".encode()).hexdigest()
            if r['batch_id']!=batch or r['hash_linha']!=sha256(r['payload_json'].encode()).hexdigest():raise ValueError('Hash/batch divergente')
            if r['schema_version']!=version or r['timestamp_ingestao']!=r['ingerido_em'] or r['data_ingestao']!=r['ingerido_em'].date():raise ValueError('Versão/timestamp divergente')
            prefix=f'/Volumes/{config.catalogo}/{config.schema("landing")}/arquivos/cenarios/v2/'
            if r['arquivo_origem']!=prefix+r['data_referencia']+'/'+r['arquivo']:raise ValueError('Caminho divergente')
            if r['batch_id_origem']!='DERIVADO_CENARIO_DATA_LOTE_LEGADO':raise ValueError('Proveniência batch divergente')
        report[name]=len(rows);print(name,'METADADOS BRONZE: OK',len(rows))
    validar_bronze(spark,config) # Reconfere preservação após DDL das views.
    print('CONTRATO BRONZE: OK');print(report)
    return report
