import csv
import io
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from medallion.synthetic.contracts import CONTRACTS
from medallion.synthetic.generator import gerar_lotes, arquivos_planejados
from medallion.synthetic.publish import publicar, conferir


class SyntheticTests(unittest.TestCase):
    def test_contracts_and_serialization(self):
        for path, (data, count, fonte, _) in arquivos_planejados().items():
            rows = ([json.loads(line) for line in data.decode().splitlines()] if path.endswith('.json')
                    else list(csv.DictReader(io.StringIO(data.decode()))))
            self.assertEqual(len(rows), count)
            for row in rows:
                self.assertTrue(set(CONTRACTS[fonte]) <= row.keys())
        self.assertEqual(arquivos_planejados(), arquivos_planejados())
        self.assertNotEqual(arquivos_planejados(), arquivos_planejados('2026-02-15'))

    def test_temporal_and_quality_cases(self):
        a, b, c = gerar_lotes().values()
        self.assertEqual(a['transacoes'][0], a['transacoes'][1])
        self.assertEqual(a['transacoes'][0], b['transacoes'][0])
        versions = [a['clientes_cdc'][0], b['clientes_cdc'][0], c['clientes_cdc'][0]]
        self.assertLess(versions[0]['data_atualizacao'], versions[2]['data_atualizacao'])
        self.assertLess(versions[2]['data_atualizacao'], versions[1]['data_atualizacao'])
        self.assertNotIn('dispositivo', a['transacoes'][0])
        self.assertIn('dispositivo', b['transacoes'][1])
        self.assertLess(c['transacoes'][1]['data_transacao'], a['transacoes'][0]['data_transacao'])
        cancelado = b['cartoes_cdc'][1]
        self.assertEqual(cancelado['status_cartao'], 'CANCELADO')
        self.assertLess(cancelado['data_atualizacao'], b['transacoes'][2]['data_transacao'])
        self.assertEqual(a['contas_cdc'][0]['id_cliente'], a['contas_cdc'][1]['id_cliente'])
        self.assertNotIn(a['cartoes_cdc'][-1]['id_conta'], {r['id_conta'] for r in a['contas_cdc']})
        self.assertEqual(a['estornos'][0]['valor_estorno'], '50.00')
        self.assertEqual(b['estornos'][0]['valor_estorno'], a['transacoes'][3]['valor'])
        # A transação do mês anterior precisa ter cadastro vigente naquele dia.
        self.assertLess(a['cartoes_cdc'][2]['data_atualizacao'], c['transacoes'][1]['data_transacao'])
        valid_ids = {'T001', 'T002', 'T003', 'T004', 'T006', 'T007', 'T008'}
        txs = {r['id_transacao']: r for lote in (a,b,c) for r in lote['transacoes'] if r['id_transacao'] in valid_ids}
        refunds = [r for lote in (a,b,c) for r in lote['estornos'] if r['id_transacao'] in valid_ids]
        total = sum(Decimal(r['valor']) for r in txs.values())-sum(Decimal(r['valor_estorno']) for r in refunds)
        self.assertEqual(total, Decimal('2270.00'))

    def test_repeat_resume_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            first = publicar(temp)
            self.assertGreater(first['novos_arquivos'], 0)
            pasta = Path(first['pasta'])
            times = {p: p.stat().st_mtime_ns for p in pasta.rglob('*') if p.is_file()}
            self.assertEqual(publicar(temp)['novos_arquivos'], 0)
            self.assertEqual(times, {p: p.stat().st_mtime_ns for p in times})
            self.assertEqual(conferir(temp, '2026-01-15'), first['manifesto']['arquivos'])
            manifest = pasta/'manifesto.json'; manifest.unlink()
            self.assertEqual(publicar(temp)['novos_arquivos'], 1)
            target = pasta/first['manifesto']['arquivos'][0]['caminho']
            target.write_bytes(b'corrompido')
            with self.assertRaises(ValueError): publicar(temp)
            with self.assertRaises(ValueError): conferir(temp, '2026-01-15')
            self.assertEqual(target.read_bytes(), b'corrompido')

    def test_unexpected_file_and_invalid_date(self):
        with tempfile.TemporaryDirectory() as temp:
            result = publicar(temp)
            (Path(result['pasta'])/'arquivo_extra.csv').write_text('extra')
            with self.assertRaises(ValueError): publicar(temp)
        with self.assertRaises(ValueError): arquivos_planejados('2026-02-30')
        with self.assertRaises(ValueError): arquivos_planejados('../2026-01-15')
