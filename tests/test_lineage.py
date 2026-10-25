import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from medallion.governance.lineage import plano,garantir_aresta
class API:
 def __init__(self):self.edges=[];self.posts=0
 def do(self,method,path,query=None,body=None):
  if method=='POST':self.edges.append(body);self.posts+=1;return body
  return {'external_lineage_relationships':[{'external_lineage_info':r} for r in self.edges]}
class LineageTests(unittest.TestCase):
 def test_graph_coverage_and_no_cycles(self):
  p=plano('workspace');self.assertEqual(len(p),15);self.assertEqual(len({r['bridge'] for r in p}),15)
  deps={r['target']:r['sources'] for r in p}
  def visit(t,path):
   self.assertNotIn(t,path)
   for s in deps.get(t,[]):visit(s,path+[t])
  for target in deps:visit(target,[])
  self.assertTrue(all('silver_' in s for r in p if '.medallion_dev_ouro.' in r['target'] for s in r['sources']))
 def test_repeat(self):
  a=API();s={'table':{'name':'workspace.s.t'}};t={'external_metadata':{'name':'b'}}
  self.assertEqual(garantir_aresta(a,s,t,'b','UPSTREAM'),1)
  self.assertEqual(garantir_aresta(a,s,t,'b','UPSTREAM'),0);self.assertEqual(a.posts,1)
 def test_bad_catalog(self):
  with self.assertRaises(ValueError):plano('workspace;drop')
