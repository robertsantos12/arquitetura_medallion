import copy,csv,io,json,unittest
from decimal import Decimal
from datetime import datetime,timezone
from medallion.synthetic.generator import gerar_lotes
from medallion.synthetic.generator_v2 import arquivos_planejados_v2
from medallion.synthetic.contracts import CONTRACTS
from medallion.silver.transform import transformar,canonical,semantica
from medallion.gold.transform import construir
from medallion.pipeline.storage import SILVER,GOLD,normalize,fingerprint


def fixture():
    return {f:[r for l in gerar_lotes().values() for r in l[f]] for f in CONTRACTS}


class HomologacaoTests(unittest.TestCase):
    def test_v1_financeiro_temporal_quarentena(self):
        s=transformar(fixture());g=construir(s,'2026-05-31')
        oracle={'T001':100,'T002':150,'T003':0,'T004':400,'T006':1500,'T007':70,'T008':50,'T_CANCEL':0}
        self.assertEqual({r['id_transacao']:r['valor_liquido'] for r in g['gold_fato_transacao']},oracle)
        self.assertEqual(sum(r['valor_liquido'] for r in g['gold_cliente_mes']),Decimal('2270'))
        self.assertEqual(len(s['quarentena']),8)
        vs=sorted([r for r in s['clientes_cdc'] if r['id_cliente']=='C001'],key=lambda r:r['vigente_desde'])
        self.assertEqual(len(vs),3);self.assertEqual(vs[0]['vigente_ate'],vs[1]['vigente_desde'])
        self.assertEqual(vs[1]['vigente_ate'],vs[2]['vigente_desde'])
        t={r['id_transacao']:r for r in s['transacoes']}
        self.assertEqual(t['T001']['cidade'],'Porto Alegre');self.assertEqual(t['T004']['cidade'],'Canoas')
        self.assertEqual(t['T007']['cliente_versao'],vs[1]['row_key'])

    def test_cutoff_refunds_and_future(self):
        s=transformar(fixture());g=construir(s,'2026-01-15')
        tx={r['id_transacao']:r for r in g['gold_fato_transacao']}
        self.assertEqual(tx['T002']['valor_liquido'],200)
        self.assertEqual(tx['T003']['valor_liquido'],300)
        self.assertNotIn('T004',tx);self.assertNotIn('T006',tx)
        self.assertTrue(all(r['dias_desde_ultima_compra']>=0 for r in g['gold_features_cliente'] if r['dias_desde_ultima_compra'] is not None))

    def test_conflicts_refusal_and_excessive_refunds(self):
        o=fixture();o['transacoes'].append(dict(o['transacoes'][0],valor='101.00'))
        s=transformar(o);self.assertNotIn('T001',{r['id_transacao'] for r in s['transacoes']})
        self.assertEqual(sum(r['motivo']=='conflito_mesma_chave' for r in s['quarentena']),2)
        o=fixture();o['estornos'].append(dict(o['estornos'][0],id_estorno='S_EXTRA',valor_estorno='180.00'))
        s=transformar(o);self.assertFalse(any(r['id_transacao']=='T002' for r in s['estornos']))
        self.assertEqual(sum('excede' in r['motivo'] for r in s['quarentena']),2)
        o=fixture();o['transacoes'].append(dict(o['transacoes'][0],id_transacao='REC',status_transacao='RECUSADA'))
        s=transformar(o);g=construir(s,'2026-05-31')
        self.assertEqual(next(r['valor_liquido'] for r in g['gold_fato_transacao'] if r['id_transacao']=='REC'),0)

    def test_v2_serialized_full_mass_and_repetition(self):
        o={f:[] for f in CONTRACTS}
        for p,(b,n,f,l) in arquivos_planejados_v2().items():
            rows=[json.loads(x) for x in b.decode().splitlines()] if p.endswith('.json') else list(csv.DictReader(io.StringIO(b.decode())))
            o[f].extend(rows)
        self.assertEqual(len(o['transacoes']),12158)
        s=transformar(o);g=construir(s,'2026-05-31')
        self.assertEqual(len(s['transacoes']),12153);self.assertEqual(len(s['quarentena']),8)
        self.assertEqual(sum(r['valor_liquido'] for r in g['gold_fato_transacao'] if r['id_transacao'].startswith('T')),2270)
        self.assertEqual(sum(r['valor_liquido'] for r in g['gold_cliente_mes']),sum(r['valor_liquido'] for r in g['gold_fato_transacao']))
        self.assertTrue(all(r['valor_liquido']==0 for r in g['gold_fato_transacao'] if r['status_transacao']!='APROVADA'))
        self.assertEqual(sum(r['status_transacao']=='RECUSADA' for r in g['gold_fato_transacao']),21)
        for f in CONTRACTS:
            self.assertEqual(len({canonical(semantica(f,r)) for r in o[f]}),len(s[f])+sum(r['fonte']==f for r in s['quarentena']))
        reversed_o={f:list(reversed(rs)) for f,rs in o.items()}
        s2=transformar(reversed_o);g2=construir(s2,'2026-05-31')
        for f,cols in SILVER.items():self.assertEqual(fingerprint(normalize(s[f],cols)),fingerprint(normalize(s2[f],cols)))
        for f,cols in GOLD.items():self.assertEqual(fingerprint(normalize(g[f],cols)),fingerprint(normalize(g2[f],cols)))

    def test_timestamp_and_tombstone(self):
        self.assertEqual(canonical({'t':datetime(2026,1,1)}),canonical({'t':datetime(2026,1,1,tzinfo=timezone.utc)}))
        o=fixture();o['cartoes_cdc'].append(dict(o['cartoes_cdc'][0],operacao='D',data_atualizacao='2026-01-16T00:00:00+00:00'))
        s=transformar(o);self.assertNotIn('T007',{r['id_transacao'] for r in s['transacoes']});self.assertIn('T004',{r['id_transacao'] for r in s['transacoes']})
