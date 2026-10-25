from collections import defaultdict
from datetime import date, datetime, time, timezone
from decimal import Decimal
from medallion.silver.transform import digest

ZERO=Decimal('0.00')


def construir(silver, data_corte):
    corte=datetime.combine(date.fromisoformat(data_corte),time.max,timezone.utc)
    refunds=defaultdict(lambda:ZERO);risk=defaultdict(list)
    for r in silver['estornos']:
        if r['data_estorno']<=corte: refunds[r['id_transacao']]+=r['valor_estorno']
    for r in silver['eventos_risco']:
        if r['data_evento']<=corte: risk[r['id_transacao']].append(r)
    facts=[];monthly=defaultdict(list);indicators=[]
    for t in silver['transacoes']:
        if t['data_transacao']>corte: continue
        aprovado=t['status_transacao']=='APROVADA'
        bruto=t['valor'] if aprovado else ZERO
        estorno=refunds[t['id_transacao']]
        if estorno>bruto: raise ValueError('estorno excedente')
        f={**t,'valor_bruto':bruto,'valor_estornado':estorno,'valor_liquido':bruto-estorno,
           'data_corte':date.fromisoformat(data_corte),'mes':t['data_transacao'].date().replace(day=1),
           'id_estabelecimento':digest(t['estabelecimento'])}
        facts.append(f);monthly[(f['id_cliente'],f['mes'])].append(f)
        events=risk[t['id_transacao']]
        indicators.append(dict(row_key=t['id_transacao'],id_transacao=t['id_transacao'],id_cliente=t['id_cliente'],
            eventos=len(events),chargebacks=sum(e['tipo_evento']=='CHARGEBACK' for e in events),
            valor_estornado=estorno,data_corte=date.fromisoformat(data_corte)))
    months=[]
    for (client,mes),rs in sorted(monthly.items()):
        months.append(dict(row_key=digest([client,mes]),id_cliente=client,mes=mes,tentativas=len(rs),
            aprovadas=sum(r['status_transacao']=='APROVADA' for r in rs),
            recusadas=sum(r['status_transacao']=='RECUSADA' for r in rs),
            canceladas=sum(r['status_transacao']=='CANCELADA' for r in rs),
            valor_bruto=sum((r['valor_bruto'] for r in rs),ZERO),valor_estornado=sum((r['valor_estornado'] for r in rs),ZERO),
            valor_liquido=sum((r['valor_liquido'] for r in rs),ZERO)))
    features=[]
    clients=defaultdict(list)
    for f in facts: clients[f['id_cliente']].append(f)
    for client,rs in sorted(clients.items()):
        approved=[r for r in rs if r['status_transacao']=='APROVADA']
        features.append(dict(row_key=client,id_cliente=client,data_corte=date.fromisoformat(data_corte),
            tentativas=len(rs),aprovadas=len(approved),recusadas=sum(r['status_transacao']=='RECUSADA' for r in rs),
            valor_liquido=sum((r['valor_liquido'] for r in rs),ZERO),
            dias_desde_ultima_compra=(corte.date()-max(r['data_transacao'] for r in approved).date()).days if approved else None))
    lojas={r['id_estabelecimento']:dict(row_key=r['id_estabelecimento'],id_estabelecimento=r['id_estabelecimento'],estabelecimento=r['estabelecimento']) for r in facts}
    return {'gold_fato_transacao':facts,'gold_cliente_mes':months,'gold_indicadores_risco':indicators,
            'gold_features_cliente':features,'gold_dim_cliente':[r for r in silver['clientes_cdc'] if r['vigente_desde']<=corte],
            'gold_dim_conta':[r for r in silver['contas_cdc'] if r['vigente_desde']<=corte],
            'gold_dim_cartao':[r for r in silver['cartoes_cdc'] if r['vigente_desde']<=corte],
            'gold_dim_estabelecimento':list(lojas.values())}
