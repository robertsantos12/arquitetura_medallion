"""Testa o protocolo de persistência; não substitui integração Delta real."""
import copy,re,unittest
from datetime import datetime,timezone
from medallion.pipeline.storage import merge

class Row(dict):
    def asDict(self):return dict(self)
class Frame:
    def __init__(self,spark,rows):self.spark=spark;self.rows=rows
    def createOrReplaceTempView(self,name):self.spark.views[name]=copy.deepcopy(self.rows)
class Catalog:
    def __init__(self,s):self.s=s
    def dropTempView(self,name):del self.s.views[name]
class Spark:
    def __init__(self):self.rows=[];self.views={};self.catalog=Catalog(self)
    def createDataFrame(self,rows,schema):return Frame(self,rows)
    def sql(self,q):
        if q.startswith('CREATE'):return self
        if q.startswith('SELECT'):return self
        if q.startswith('MERGE'):
            view=re.search(r'USING (\w+) s',q).group(1)
            keys={(r['snapshot_id'],r['row_key']) for r in self.rows}
            for row in self.views[view]:
                if (row['snapshot_id'],row['row_key']) not in keys:self.rows.append(copy.deepcopy(row))
            return self
        raise AssertionError(q)
    def collect(self):return [Row(r) for r in self.rows]

class SnapshotTests(unittest.TestCase):
    def test_insert_repeat_and_conflict_without_overwrite(self):
        spark=Spark();snapshot='a'*64
        first=merge(spark,'table',[{'row_key':'1','nome':'teste'}],['row_key','nome'],snapshot)
        self.assertEqual(first['inseridas'],1)
        second=merge(spark,'table',[{'row_key':'1','nome':'teste'}],['row_key','nome'],snapshot)
        self.assertEqual(second['inseridas'],0);self.assertEqual(first['hash'],second['hash'])
        with self.assertRaises(ValueError):merge(spark,'table',[{'row_key':'1','nome':'alterado'}],['row_key','nome'],snapshot)
        self.assertEqual(spark.rows[0]['nome'],'teste')
    def test_resume_partial_and_duplicate_keys(self):
        spark=Spark();snapshot='b'*64
        spark.rows=[{'snapshot_id':snapshot,'row_key':'1','nome':'um'}]
        result=merge(spark,'table',[{'row_key':'1','nome':'um'},{'row_key':'2','nome':'dois'}],['row_key','nome'],snapshot)
        self.assertEqual(result['inseridas'],1)
        with self.assertRaises(ValueError):merge(spark,'table',[{'row_key':'1'},{'row_key':'1'}],['row_key'],snapshot)
