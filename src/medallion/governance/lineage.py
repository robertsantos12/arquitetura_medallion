"""Linhagem declarada via API oficial. Não simula leitura/escrita de dados."""
import re
from hashlib import sha256
API='/api/2.0/lineage-tracking/'

def plano(catalog):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',catalog):raise ValueError('Catálogo inválido')
    b=lambda f:f'{catalog}.medallion_dev_bronze.raw_{f}'
    s=lambda f:f'{catalog}.medallion_dev_prata.silver_{f}'
    g=lambda f:f'{catalog}.medallion_dev_ouro.{f}'
    dims=['clientes_cdc','contas_cdc','cartoes_cdc']
    deps={s('clientes_cdc'):[b('clientes_cdc')],s('contas_cdc'):[b('contas_cdc'),s('clientes_cdc')],
          s('cartoes_cdc'):[b('cartoes_cdc'),s('contas_cdc'),s('clientes_cdc')],
          s('transacoes'):[b('transacoes')]+[s(f) for f in dims],
          s('eventos_risco'):[b('eventos_risco'),s('transacoes')],s('estornos'):[b('estornos'),s('transacoes')],
          s('quarentena'):[b(f) for f in dims+['transacoes','eventos_risco','estornos']]}
    for target in ['gold_fato_transacao','gold_cliente_mes','gold_features_cliente']:deps[g(target)]=[s('transacoes'),s('estornos')]
    deps[g('gold_indicadores_risco')]=[s('transacoes'),s('eventos_risco'),s('estornos')]
    for target,source in zip(['gold_dim_cliente','gold_dim_conta','gold_dim_cartao'],dims):deps[g(target)]=[s(source)]
    deps[g('gold_dim_estabelecimento')]=[s('transacoes')]
    return [{'bridge':'nr_python_'+sha256(t.encode()).hexdigest()[:24],'target':t,'sources':ss,
             'definition_hash':sha256('|'.join([t,*sorted(ss)]).encode()).hexdigest()} for t,ss in deps.items()]

def relacionamentos(api,bridge,direction):
    found=[];token=None;seen=set()
    while True:
        q={'object_info.external_metadata.name':bridge,'lineage_direction':direction,'page_size':1000}
        if token:q['page_token']=token
        response=api.do('GET',API+'external-lineage',query=q)
        for row in response.get('external_lineage_relationships',[]):
            info=row.get('external_lineage_info',{})
            if 'source' not in info or 'target' not in info:raise ValueError('API sem endpoints verificáveis; preservar output para revisão')
            found.append(info)
        token=response.get('next_page_token')
        if not token:return found
        if token in seen:raise ValueError('Paginação repetida')
        seen.add(token)

def garantir_aresta(api,source,target,bridge,direction):
    def matches():return [r for r in relacionamentos(api,bridge,direction) if r['source']==source and r['target']==target]
    old=matches()
    if len(old)>1:raise ValueError('Relação duplicada preexistente')
    if not old:api.do('POST',API+'external-lineage',body={'source':source,'target':target,'properties':{'nr_tipo':'declarada','nr_projeto':'novarota'}})
    if len(matches())!=1:raise ValueError('Aresta não confirmada pela API')
    return int(not old)

def registrar(spark,catalog):
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.errors import NotFound
    api=WorkspaceClient().api_client;steps=plano(catalog)
    for table in sorted({t for p in steps for t in [p['target'],*p['sources']]}):
        spark.sql('DESCRIBE TABLE '+'.'.join('`'+part+'`' for part in table.split('.'))).collect()
    created=0
    for p in steps:
        body={'name':p['bridge'],'system_type':'DATABRICKS','entity_type':'python_transformation',
              'description':'NovaRota: transformação Python no driver; dependências declaradas, não captura nativa. Destino: '+p['target'],
              'properties':{'nr_projeto':'novarota','nr_tipo':'declarada','nr_definition_hash':p['definition_hash']}}
        try:old=api.do('GET',API+'external-metadata/'+p['bridge'])
        except NotFound:
            api.do('POST',API+'external-metadata',body=body)
            old=api.do('GET',API+'external-metadata/'+p['bridge'])
        if old.get('properties',{}).get('nr_definition_hash')!=p['definition_hash'] or old.get('properties',{}).get('nr_projeto')!='novarota':raise ValueError('Metadado incompatível; não será sobrescrito: '+p['bridge'])
        bridge={'external_metadata':{'name':p['bridge']}}
        for source in p['sources']:created+=garantir_aresta(api,{'table':{'name':source}},bridge,p['bridge'],'UPSTREAM')
        created+=garantir_aresta(api,bridge,{'table':{'name':p['target']}},p['bridge'],'DOWNSTREAM')
        print(p['target'],'LINHAGEM DECLARADA RELIDA: OK',p['bridge'])
    result={'transformacoes':len(steps),'arestas':sum(len(p['sources'])+1 for p in steps),'novas_arestas':created}
    print('LINHAGEM DECLARADA: OK',result)
    return result
