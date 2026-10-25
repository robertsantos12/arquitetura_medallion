import unittest

from medallion.config import PipelineConfig


class ConfigTest(unittest.TestCase):
    def test_ambientes_isolam_schemas(self):
        dev = PipelineConfig(ambiente="dev")
        prod = PipelineConfig(ambiente="prod")
        self.assertEqual(dev.schema_sql("bronze"), "`workspace`.`medallion_dev_bronze`")
        self.assertNotEqual(dev.schema("bronze"), prod.schema("bronze"))
        self.assertEqual(dev.caminho_entrada, "/Volumes/workspace/medallion_dev_landing/arquivos")

    def test_rejeita_identificadores_sql(self):
        for nome in ("workspace; DROP TABLE x", "a.b", "", "a`b"):
            with self.subTest(nome=nome), self.assertRaises(ValueError):
                PipelineConfig(catalogo=nome)
        with self.assertRaises(ValueError):
            PipelineConfig().tabela_sql("ouro", "a.b")

    def test_reprocessamento_exige_data_valida(self):
        for data in (None, "2026-02-30", "20261024", "2026-1-01"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                PipelineConfig(modo="reprocessamento", data_referencia=data)
        config = PipelineConfig(modo="reprocessamento", data_referencia="2026-10-24")
        self.assertEqual(config.data_referencia, "2026-10-24")

    def test_parametros_invalidos(self):
        for kwargs in ({"ambiente": "teste"}, {"modo": "overwrite"}, {"batch_id": ""},
                       {"batch_id": "a/b"}, {"raiz_arquivos": "dbfs:/tmp"},
                       {"raiz_arquivos": "/Volumes/a/b"},
                       {"raiz_arquivos": "/Volumes/a/b/c/../x"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PipelineConfig(**kwargs)
        with self.assertRaises(ValueError):
            PipelineConfig().schema("inexistente")

    def test_batch_pode_ser_fixado_para_retentativa(self):
        a, b = PipelineConfig(), PipelineConfig()
        self.assertNotEqual(a.batch_id, b.batch_id)
        self.assertEqual(PipelineConfig(batch_id=a.batch_id).batch_id, a.batch_id)


if __name__ == "__main__":
    unittest.main()
