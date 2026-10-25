import unittest
from unittest.mock import Mock

from medallion.bootstrap import preparar_ambiente
from medallion.config import PipelineConfig


class BootstrapTest(unittest.TestCase):
    def test_bloqueia_producao_antes_de_acessar_spark(self):
        spark = Mock()
        with self.assertRaises(ValueError):
            preparar_ambiente(spark, PipelineConfig(ambiente="prod"))
        spark.sql.assert_not_called()

    def test_falha_de_permissao_interrompe_e_propaga(self):
        spark = Mock()
        spark.sql.side_effect = PermissionError("Sem CREATE SCHEMA")
        with self.assertLogs("medallion", level="ERROR"), self.assertRaises(PermissionError):
            preparar_ambiente(spark, PipelineConfig())
        self.assertEqual(spark.sql.call_count, 1)


if __name__ == "__main__":
    unittest.main()
