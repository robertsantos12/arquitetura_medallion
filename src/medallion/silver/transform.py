"""Reconstituição temporal completa por cenário pequeno, com quarentena rastreável."""
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from hashlib import sha256
from medallion.quality import instante, dinheiro
from medallion.synthetic.contracts import CONTRACTS

KEYS = dict(zip(CONTRACTS, ('id_cliente','id_conta','id_cartao','id_transacao','id_evento','id_estorno')))


def canonical(row):
    def encode(v):
        if isinstance(v, datetime):
            return v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.astimezone(timezone.utc).isoformat()
        return str(v)
    return json.dumps(row, sort_keys=True, ensure_ascii=False, default=encode, separators=(',', ':'))


def digest(row):
    return sha256(canonical(row).encode()).hexdigest()


def vigente(rows, key, value, when):
    found = [r for r in rows if r[key] == value and r['vigente_desde'] <= when and (r['vigente_ate'] is None or when < r['vigente_ate'])]
    if len(found) > 1:
        raise ValueError('Sobreposição temporal')
    return found[0] if found and found[0]['operacao'] != 'D' else None


def semantica(fonte, row):
    # CSV adiciona células vazias para campos opcionais de outras linhas.
    return {k:v for k,v in row.items() if k in CONTRACTS[fonte] or v not in ('',None)}


def transformar(origem):
    out = {f: [] for f in CONTRACTS}
    out['quarentena'] = []
    stats = {}

    def reject(fonte, row, motivo):
        out['quarentena'].append({'fonte': fonte, 'id_origem': str(row.get(KEYS[fonte], '')),
            'motivo': motivo, 'payload_json': canonical(row), 'row_key': digest([fonte, row, motivo])})

    def unique(fonte):
        groups = defaultdict(dict)
        for raw in origem[fonte]:
            r = semantica(fonte, raw)
            try:
                if any(k not in r or r[k] is None or str(r[k]).strip()=='' for k in CONTRACTS[fonte]):
                    raise ValueError('campo obrigatorio ausente')
                if fonte.endswith('_cdc'):
                    instante(r['data_atualizacao'])
                key = str(r[KEYS[fonte]]) + ('|' + r['data_atualizacao'] if fonte.endswith('_cdc') else '')
                groups[key][canonical(r)] = r
            except (ValueError, TypeError) as e:
                reject(fonte, r, str(e))
        valid=[]
        for variants in groups.values():
            if len(variants)>1:
                for r in variants.values(): reject(fonte,r,'conflito_mesma_chave')
            else: valid.append(next(iter(variants.values())))
        stats[fonte]={'origem':len(origem[fonte]), 'candidatos_unicos':len(valid)}
        return sorted(valid,key=canonical)

    for fonte, key in list(KEYS.items())[:3]:
        valid=[]
        for row in unique(fonte):
            r=dict(row)
            try:
                r['data_atualizacao']=instante(r['data_atualizacao'])
                if r['operacao'] not in ('I','U','D'): raise ValueError('operacao CDC invalida')
                if fonte=='clientes_cdc':
                    r['renda']=dinheiro(r['renda'])
                    if r['estado'] not in ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'): raise ValueError('UF invalida')
                    if not r['cpf'].startswith('CPF_SINTETICO_'): raise ValueError('token CPF invalido')
                elif fonte=='contas_cdc':
                    r['data_abertura']=date.fromisoformat(r['data_abertura'])
                    if r['data_abertura'] > r['data_atualizacao'].date(): raise ValueError('abertura futura')
                    if r['status_conta'] not in ('ATIVA','ENCERRADA','BLOQUEADA'): raise ValueError('status conta invalido')
                    if not vigente(out['clientes_cdc'],'id_cliente',r['id_cliente'],r['data_atualizacao']): raise ValueError('cliente temporal inexistente')
                else:
                    r['limite']=dinheiro(r['limite'])
                    if r['status_cartao'] not in ('ATIVO','CANCELADO','BLOQUEADO'): raise ValueError('status cartao invalido')
                    a=vigente(out['contas_cdc'],'id_conta',r['id_conta'],r['data_atualizacao'])
                    if not a or not vigente(out['clientes_cdc'],'id_cliente',a['id_cliente'],r['data_atualizacao']): raise ValueError('conta cliente temporal inexistente')
                r['payload_json']=canonical(row);valid.append(r)
            except (ValueError,TypeError) as e: reject(fonte,row,str(e))
        groups=defaultdict(list)
        for r in valid: groups[r[key]].append(r)
        for versions in groups.values():
            versions.sort(key=lambda r:r['data_atualizacao'])
            for i,r in enumerate(versions):
                r.update(vigente_desde=r['data_atualizacao'],vigente_ate=versions[i+1]['data_atualizacao'] if i+1<len(versions) else None)
                r['row_key']=digest([r[key],r['vigente_desde']]);out[fonte].append(r)

    for row in unique('transacoes'):
        r=dict(row)
        try:
            r['valor']=dinheiro(r['valor'],True);r['data_transacao']=instante(r['data_transacao'])
            if r.get('status_transacao') not in ('APROVADA','RECUSADA','CANCELADA'): raise ValueError('status transacao invalido')
            if r['moeda']!='BRL': raise ValueError('moeda nao suportada')
            k=vigente(out['cartoes_cdc'],'id_cartao',r['id_cartao'],r['data_transacao'])
            a=vigente(out['contas_cdc'],'id_conta',k['id_conta'],r['data_transacao']) if k else None
            c=vigente(out['clientes_cdc'],'id_cliente',a['id_cliente'],r['data_transacao']) if a else None
            if not k or not a or not c: raise ValueError('vinculo temporal inexistente')
            if k['status_cartao']!='ATIVO' or a['status_conta']!='ATIVA': raise ValueError('cartao ou conta inativo')
            r.update(id_conta=a['id_conta'],id_cliente=c['id_cliente'],nome=c['nome'],cidade=c['cidade'],segmento=c['segmento'],
                     cliente_versao=c['row_key'],conta_versao=a['row_key'],cartao_versao=k['row_key'],payload_json=canonical(row),row_key=r['id_transacao'])
            out['transacoes'].append(r)
        except (ValueError,TypeError) as e: reject('transacoes',row,str(e))
    tx={r['id_transacao']:r for r in out['transacoes']}
    refunds=defaultdict(list)
    for fonte, dt in [('eventos_risco','data_evento'),('estornos','data_estorno')]:
        for row in unique(fonte):
            r=dict(row)
            try:
                r[dt]=instante(r[dt]); t=tx.get(r['id_transacao'])
                if not t: raise ValueError('transacao inexistente ou invalida')
                if r[dt]<t['data_transacao']: raise ValueError('evento anterior a transacao')
                if fonte=='eventos_risco':
                    if r['tipo_evento'] not in ('SUSPEITA','FRAUDE','CHARGEBACK') or r['severidade'] not in ('BAIXA','MEDIA','ALTA'): raise ValueError('dominio risco invalido')
                else:
                    r['valor_estorno']=dinheiro(r['valor_estorno'],True)
                    if t['status_transacao']!='APROVADA': raise ValueError('estorno de tentativa nao aprovada')
                r.update(payload_json=canonical(row),row_key=r[KEYS[fonte]])
                if fonte=='estornos': refunds[r['id_transacao']].append(r)
                else: out[fonte].append(r)
            except (ValueError,TypeError) as e: reject(fonte,row,str(e))
    for id_, group in refunds.items():
        if sum(r['valor_estorno'] for r in group)>tx[id_]['valor']:
            for r in group: reject('estornos',json.loads(r['payload_json']),'estorno acumulado excede compra')
        else: out['estornos'].extend(group)
    out['estatisticas']=stats
    return out
