"""Aplicação retomável de comentários, tags e PK. Sem mutações de linhas."""
import json
import re
from pathlib import Path


def ident(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',value):raise ValueError('Identificador inválido')
    return '`'+value+'`'


def literal(value):
    # Metadados versionados, sem sequências de escape SQL.
    if '\\' in value:raise ValueError('Escape não suportado no metadado')
    return "'"+value.replace("'","''")+"'"


def rows(spark,sql):return [r.asDict() for r in spark.sql(sql).collect()]


def metadata(spark,catalog,table):
    root=ident(catalog)+'.information_schema.'
    filt=f"table_catalog={literal(catalog)} AND table_schema='medallion_dev_ouro' AND table_name={literal(table)}"
    cols=rows(spark,'SELECT column_name,comment,is_nullable FROM '+root+'columns WHERE '+filt)
    constraints=rows(spark,"SELECT constraint_name FROM "+root+"table_constraints WHERE "+filt+" AND constraint_type='PRIMARY KEY'")
    pk=[]
    if len(constraints)>1:raise ValueError('Múltiplas PKs inesperadas')
    if constraints:
        pk=[r['column_name'] for r in rows(spark,'SELECT column_name FROM '+root+'key_column_usage WHERE '+filt+' AND constraint_name='+literal(constraints[0]['constraint_name'])+' ORDER BY ordinal_position')]
    tag_filter=filt.replace('table_catalog=', 'catalog_name=').replace('table_schema=', 'schema_name=')
    tt=rows(spark,'SELECT tag_name,tag_value FROM '+root+'table_tags WHERE '+tag_filter)
    ct=rows(spark,'SELECT column_name,tag_name,tag_value FROM '+root+'column_tags WHERE '+tag_filter)
    return {'columns':{r['column_name']:r for r in cols},'pk':pk,'table_tags':{r['tag_name']:r['tag_value'] for r in tt},
            'column_tags':{(r['column_name'],r['tag_name']):r['tag_value'] for r in ct}}


def validar_definicao(spec):
    for table,m in spec.items():
        ident(table)
        if not m['primary_key'] or not set(m['primary_key'])<=m['columns'].keys():raise ValueError('PK fora das colunas')
        if len(set(m['primary_key']))!=len(m['primary_key']):raise ValueError('PK repetida')
        if 'snapshot_id' not in m['primary_key']:raise ValueError('PK precisa de snapshot_id')
        for col,c in m['columns'].items():
            ident(col)
            if not c['descricao'].strip():raise ValueError('Descrição vazia')
            if (c['tags']['nr_papel']=='pk')!=(col in m['primary_key']):raise ValueError('Tag PK inconsistente')


def aplicar(spark,catalog,raiz):
    ident(catalog)
    spec=json.loads((Path(raiz)/'docs/gold_colunas.json').read_text())
    validar_definicao(spec)
    # Pré-validação de TODAS as tabelas antes da primeira alteração.
    for table,m in spec.items():
        full=ident(catalog)+'.`medallion_dev_ouro`.'+ident(table)
        current=metadata(spark,catalog,table)
        if set(current['columns'])!=set(m['columns']):raise ValueError('Schema diverge do dicionário: '+table)
        if current['pk'] and current['pk']!=m['primary_key']:raise ValueError('PK preexistente incompatível: '+table)
        keys=','.join(ident(k) for k in m['primary_key'])
        nulls=' OR '.join(ident(k)+' IS NULL' for k in m['primary_key'])
        if rows(spark,f'SELECT 1 FROM {full} WHERE {nulls} LIMIT 1'):raise ValueError('PK nula: '+table)
        if rows(spark,f'SELECT {keys} FROM {full} GROUP BY {keys} HAVING count(*)>1 LIMIT 1'):raise ValueError('PK duplicada: '+table)
        for key,value in m['tags'].items():
            if key in current['table_tags'] and current['table_tags'][key]!=value:raise ValueError('Conflito de tag: '+table+'.'+key)
        for col,c in m['columns'].items():
            for key,value in c['tags'].items():
                old=current['column_tags'].get((col,key))
                if old is not None and old!=value:raise ValueError('Conflito de tag: '+table+'.'+col+'.'+key)
        print(table,'PRÉ-VALIDAÇÃO: OK')
    for table,m in spec.items():
        full=ident(catalog)+'.`medallion_dev_ouro`.'+ident(table)
        current=metadata(spark,catalog,table)
        for col,c in m['columns'].items():
            if current['columns'][col]['comment']!=c['descricao']:
                spark.sql(f'ALTER TABLE {full} ALTER COLUMN {ident(col)} COMMENT {literal(c["descricao"])}')
            for key,value in c['tags'].items():
                if current['column_tags'].get((col,key))!=value:
                    spark.sql(f'ALTER TABLE {full} ALTER COLUMN {ident(col)} SET TAGS ({literal(key)}={literal(value)})')
        for key,value in m['tags'].items():
            if current['table_tags'].get(key)!=value:spark.sql(f'ALTER TABLE {full} SET TAGS ({literal(key)}={literal(value)})')
        for key in m['primary_key']:
            if current['columns'][key]['is_nullable']=='YES':spark.sql(f'ALTER TABLE {full} ALTER COLUMN {ident(key)} SET NOT NULL')
        if not current['pk']:
            keys=','.join(ident(k) for k in m['primary_key'])
            spark.sql(f'ALTER TABLE {full} ADD CONSTRAINT {ident("pk_nr_"+table)} PRIMARY KEY ({keys})')
        after=metadata(spark,catalog,table)
        if after['pk']!=m['primary_key']:raise ValueError('PK não confirmada')
        for key in m['primary_key']:
            if after['columns'][key]['is_nullable']!='NO':raise ValueError('NOT NULL não confirmado')
        for key,value in m['tags'].items():
            if after['table_tags'].get(key)!=value:raise ValueError('Tag tabela não confirmada')
        for col,c in m['columns'].items():
            if after['columns'][col]['comment']!=c['descricao']:raise ValueError('Comentário não confirmado')
            for key,value in c['tags'].items():
                if after['column_tags'].get((col,key))!=value:raise ValueError('Tag coluna não confirmada')
        print(table,'COLUNAS, PK E TAGS: OK',json.dumps(m['primary_key']))
    print('GOVERNANÇA GOLD: OK')
    return {'tabelas':len(spec),'colunas':sum(len(m['columns']) for m in spec.values())}
