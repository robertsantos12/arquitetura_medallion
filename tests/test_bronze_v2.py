import json
import tempfile
import unittest
from pathlib import Path
from medallion.bronze.ingest_v2 import carregar_manifesto, preparar_lote, validar_lote, _linhas_arquivo
from medallion.synthetic.publish_v2 import publicar_v2
from medallion.synthetic.contracts import CONTRACTS

class BronzeV2Tests(unittest.TestCase):
    def test_lotes_e_manifesto(self):
        with tempfile.TemporaryDirectory() as raiz:
            pub=publicar_v2(raiz)
            pasta,manifesto,digest=carregar_manifesto(raiz,"2026-01-15")
            self.assertIn("/v2/",str(pasta))
            self.assertEqual(digest,pub["manifesto_sha256"])
            totais={}
            for lote in ("01_inicial","02_incremental","03_atrasado"):
                itens,_=preparar_lote(raiz,"2026-01-15",lote)
                totais[lote]=sum(len(r) for _,r in itens if _["fonte"]=="transacoes")
                self.assertGreater(len(itens),0)
                self.assertEqual({i["fonte"] for i,_ in itens},set(CONTRACTS) if lote!="03_atrasado" else {"clientes_cdc","transacoes","estornos"})
            self.assertEqual(totais,{"01_inicial":6080,"02_incremental":4560,"03_atrasado":1518})

    def test_rejeita_corrupcao_antes_da_ingestao(self):
        with tempfile.TemporaryDirectory() as raiz:
            publicar_v2(raiz)
            pasta,manifesto,_=carregar_manifesto(raiz,"2026-01-15")
            item=next(a for a in manifesto["arquivos"] if a["lote"]=="01_inicial")
            arquivo=pasta/item["caminho"]
            arquivo.write_bytes(b"corrompido")
            with self.assertRaisesRegex(ValueError,"SHA256"):
                preparar_lote(raiz,"2026-01-15","01_inicial")

    def test_caminhos_manifesto_e_lotes(self):
        with tempfile.TemporaryDirectory() as raiz:
            publicar_v2(raiz)
            pasta=Path(raiz)/"cenarios"/"v2"/"2026-01-15"
            arq=pasta/"manifesto.json"
            obj=json.loads(arq.read_text())
            obj["arquivos"][0]["caminho"]="../escape"
            arq.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):
                carregar_manifesto(raiz,"2026-01-15")
        with self.assertRaises(ValueError):
            validar_lote("04_invalido")

    def test_repeatable_plan(self):
        with tempfile.TemporaryDirectory() as raiz:
            publicar_v2(raiz)
            a,_=preparar_lote(raiz,"2026-01-15","01_inicial")
            b,_=preparar_lote(raiz,"2026-01-15","01_inicial")
            self.assertEqual(a,b)
