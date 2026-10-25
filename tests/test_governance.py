import copy,json,pathlib,unittest,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from medallion.governance.catalog import validar_definicao,ident,literal
class GovernanceTests(unittest.TestCase):
 def setUp(self):self.spec=json.loads((ROOT/'docs/gold_colunas.json').read_text())
 def test_all_tables_and_composite_keys(self):
  validar_definicao(self.spec);self.assertEqual(len(self.spec),8)
  for m in self.spec.values():self.assertIn('snapshot_id',m['primary_key'])
 def test_reject_wrong_key_and_tag(self):
  m=self.spec['gold_fato_transacao'];m['primary_key'].remove('snapshot_id')
  with self.assertRaises(ValueError):validar_definicao(self.spec)
  self.setUp();self.spec['gold_fato_transacao']['columns']['valor']['tags']['nr_papel']='pk'
  with self.assertRaises(ValueError):validar_definicao(self.spec)
 def test_identifier_and_literal(self):
  self.assertEqual(literal("d'água"),"'d''água'")
  with self.assertRaises(ValueError):ident('x; DROP TABLE y')
