import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from medallion.config import PipelineConfig
from medallion.bronze.metadata import select_contrato,normalizar_sql
class MetadataTests(unittest.TestCase):
 def test_semantics(self):
  sql=select_contrato(PipelineConfig(data_referencia='2026-01-15'),'transacoes',1)
  self.assertIn('sha2(b.payload_json,256) AS hash_linha',sql)
  self.assertIn("concat('v2|',b.data_referencia,'|',b.lote)",sql)
  self.assertIn('CAST(1 AS INT) AS schema_version',sql)
  self.assertIn('b.*',sql);self.assertNotIn('b.run_id AS batch_id',sql)
 def test_invalid_source_version(self):
  c=PipelineConfig()
  with self.assertRaises(ValueError):select_contrato(c,'bad',1)
  with self.assertRaises(ValueError):select_contrato(c,'transacoes',True)
 def test_repeat_sql(self):self.assertEqual(normalizar_sql('SELECT  b.*\nFROM t;'),normalizar_sql('SELECT b.* FROM t'))
