"""Recalcula fontes e compara snapshots persistidos, somente leitura."""
from decimal import Decimal
from medallion.bronze.validate import validar_bronze
from medallion.silver.transform import transformar
from medallion.gold.transform import construir
from medallion.pipeline.storage import SILVER,GOLD,read,normalize,fingerprint


def validar(spark,config,snapshot_silver,snapshot_gold,corte):
    origin,metrics=validar_bronze(spark,config)
    s=read(spark,config,'silver',snapshot_silver);g=read(spark,config,'gold',snapshot_gold)
    expected_s=transformar(origin)
    for name,cols in SILVER.items():
        if fingerprint(normalize(s[name],cols))!=fingerprint(normalize(expected_s[name],cols)):
            raise ValueError('Silver divergente: '+name)
        if len({r['row_key'] for r in s[name]})!=len(s[name]):raise ValueError('Chave Silver duplicada')
    expected_g=construir(s,corte)
    for name,cols in GOLD.items():
        if fingerprint(normalize(g[name],cols))!=fingerprint(normalize(expected_g[name],cols)):
            raise ValueError('Gold divergente: '+name)
        if len({r['row_key'] for r in g[name]})!=len(g[name]):raise ValueError('Chave Gold duplicada')
    for fonte,key in [('clientes_cdc','id_cliente'),('contas_cdc','id_conta'),('cartoes_cdc','id_cartao')]:
        rows=sorted(s[fonte],key=lambda r:(r[key],r['vigente_desde']))
        for a,b in zip(rows,rows[1:]):
            if a[key]==b[key] and a['vigente_ate']!=b['vigente_desde']:raise ValueError('Intervalo SCD2 inválido')
    for r in g['gold_fato_transacao']:
        if r['status_transacao']!='APROVADA' and r['valor_liquido']!=0:raise ValueError('Gasto de tentativa não aprovada')
        if not 0<=r['valor_estornado']<=r['valor_bruto']:raise ValueError('Estorno excedente')
    # Oráculo exclusivo dos casos V1 incorporados à massa; não total V2.
    oracle={'T001':Decimal('100'),'T002':Decimal('150'),'T003':Decimal('0'),'T004':Decimal('400'),'T006':Decimal('1500'),'T007':Decimal('70'),'T008':Decimal('50')}
    subset={r['id_transacao']:r['valor_liquido'] for r in g['gold_fato_transacao'] if r['id_transacao'] in oracle}
    if subset!=oracle:raise ValueError('Oráculo V1 não atingido; verificar corte ou transformação')
    result={'bronze':metrics,'silver':{k:len(v) for k,v in s.items()},'gold':{k:len(v) for k,v in g.items()},'oraculo_v1':'2270.00'}
    print('VALIDAÇÃO FINAL: OK');print(result)
    return result
