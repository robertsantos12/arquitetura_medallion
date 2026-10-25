import csv
import io
import tempfile
import unittest
from medallion.synthetic.generator_v2 import gerar_lotes_v2, arquivos_planejados_v2, PERSONAGENS
from medallion.synthetic.publish_v2 import publicar_v2, conferir_v2

class SyntheticV2Tests(unittest.TestCase):
    def test_narrativas_e_volume(self):
        lotes=gerar_lotes_v2()
        tx=[r for lote in lotes.values() for r in lote["transacoes"]]
        clientes={r["id_cliente"] for lote in lotes.values() for r in lote["clientes_cdc"]}
        self.assertEqual(len(PERSONAGENS),18)
        self.assertGreaterEqual(len(tx),12000)
        self.assertGreaterEqual(len(clientes),18)
        self.assertEqual(sum(r["id_transacao"].startswith("V2_CAFE_") for r in tx),60)
        self.assertEqual(sum(r["id_transacao"].startswith("V2_ROSAS_") for r in tx),60)
        self.assertTrue(any(r["id_transacao"].startswith("V2_ALUGUEL_REC_") and r["status_transacao"]=="RECUSADA" for r in tx))
        self.assertTrue(any(r["id_transacao"].startswith("V2_PIRULITO_") and r["status_transacao"]=="RECUSADA" for r in tx))
        self.assertEqual(arquivos_planejados_v2(),arquivos_planejados_v2())
    def test_publicacao_isolada_e_idempotente(self):
        with tempfile.TemporaryDirectory() as temp:
            first=publicar_v2(temp)
            self.assertIn("/v2/",first["pasta"])
            self.assertEqual(conferir_v2(temp,"2026-01-15"),first["manifesto"]["arquivos"])
            self.assertEqual(publicar_v2(temp)["novos_arquivos"],0)
            self.assertEqual(publicar_v2(temp)["manifesto_sha256"],first["manifesto_sha256"])
