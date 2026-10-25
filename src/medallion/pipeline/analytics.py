"""SQL versionado e plano de execução. Sem mutações permanentes."""
from pathlib import Path
from medallion.pipeline.storage import GOLD,table,validar_snapshot,read


def analisar(spark,config,snapshot,raiz):
    validar_snapshot(snapshot)
    read(spark,config,'gold',snapshot) # Requer marcador completo.
    for name in GOLD:
        spark.sql(f"SELECT * FROM {table(config,'gold',name)} WHERE snapshot_id='{snapshot}'").createOrReplaceTempView('h_'+name)
    results={}
    for path in sorted((Path(raiz)/'sql').glob('*.sql')):
        query=path.read_text()
        print('CONSULTA:',path.name)
        df=spark.sql(query);df.show(30,truncate=False);results[path.name]=df.count()
        if path.name.startswith('01_'):
            print('PLANO PARA REVISÃO:');spark.sql('EXPLAIN FORMATTED '+query).show(200,truncate=False)
    return results
