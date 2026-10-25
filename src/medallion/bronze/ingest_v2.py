"""Bronze V2: ingestão determinística e retomável de arquivos CSV/JSON do Volume.

Preserva valores de origem como JSON e metadados; tipagem e DQ pertencem à Prata.
Um único escritor por cenário/lote. MERGE por (arquivo, número da linha).
"""
import csv
import io
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from medallion.synthetic.contracts import CONTRACTS

LOTES = ("01_inicial", "02_incremental", "03_atrasado")
FONTES = tuple(CONTRACTS)
SCHEMA_BRONZE = ("id_registro STRING, fonte STRING, lote STRING, arquivo STRING, "
                 "linha BIGINT, payload_json STRING, arquivo_sha256 STRING, "
                 "data_referencia STRING, ingerido_em TIMESTAMP, run_id STRING")
SCHEMA_CONTROLE = ("cenario STRING, data_referencia STRING, lote STRING, fonte STRING, "
                  "arquivo STRING, arquivo_sha256 STRING, registros BIGINT, "
                  "processado_em TIMESTAMP, run_id STRING")


def validar_lote(lote):
    if lote not in LOTES:
        raise ValueError(f"Lote inválido: {lote!r}; opções {LOTES}")
    return lote


def carregar_manifesto(raiz, data_referencia):
    """Valida manifesto e impede path traversal antes de qualquer escrita."""
    pasta = Path(raiz)/"cenarios"/"v2"/data_referencia
    data = (pasta/"manifesto.json").read_bytes()
    manifesto = json.loads(data)
    if (manifesto.get("cenario") != "v2" or
            manifesto.get("data_referencia") != data_referencia or
            manifesto.get("ordem_chegada") != list(LOTES) or
            manifesto.get("schema_version") != 1):
        raise ValueError("Manifesto V2 com metadados incompatíveis")
    nomes = set()
    for item in manifesto["arquivos"]:
        nome=item["caminho"]
        partes=Path(nome).parts
        if (Path(nome).is_absolute() or ".." in partes or len(partes)<3 or
                partes[0] not in LOTES or partes[1] not in FONTES or
                item["lote"] != partes[0] or item["fonte"] != partes[1] or
                nome in nomes):
            raise ValueError(f"Caminho/fonte/lote inválidos ou duplicados: {nome}")
        nomes.add(nome)
    return pasta, manifesto, sha256(data).hexdigest()


def _linhas_arquivo(path, item):
    """Lê e valida arquivo inteiro antes de devolvê-lo para escrita."""
    dados=path.read_bytes()
    digest=sha256(dados).hexdigest()
    if digest != item["sha256"]:
        raise ValueError(f"SHA256 divergente: {item['caminho']}")
    texto=dados.decode("utf-8")
    if path.suffix==".json":
        registros=[json.loads(l) for l in texto.splitlines() if l.strip()]
    elif path.suffix==".csv":
        registros=list(csv.DictReader(io.StringIO(texto)))
    else:
        raise ValueError(f"Extensão não suportada: {path.name}")
    if len(registros)!=item["registros"]:
        raise ValueError(f"Contagem de linhas divergente: {item['caminho']}")
    for r in registros:
        if not set(CONTRACTS[item["fonte"]]).issubset(r):
            raise ValueError(f"Colunas obrigatórias ausentes em {item['caminho']}")
    return registros


def preparar_lote(raiz, data_referencia, lote):
    """Pré-valida TODOS os arquivos do lote antes de iniciar a transação lógica."""
    validar_lote(lote)
    pasta, manifesto, manifest_hash=carregar_manifesto(raiz,data_referencia)
    itens=sorted((a for a in manifesto["arquivos"] if a["lote"]==lote),
                 key=lambda a:a["caminho"])
    if not itens:
        raise ValueError(f"Nenhum arquivo encontrado no lote {lote}")
    dados=[]
    for item in itens:
        registros=_linhas_arquivo(pasta/item["caminho"],item)
        dados.append((item,registros))
    return dados, manifest_hash


def _nome_bronze(config, fonte):
    return config.tabela_sql("bronze", "raw_"+fonte)


def preparar_tabelas(spark, config):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.schema_sql('bronze')}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.schema_sql('controle')}")
    for fonte in FONTES:
        spark.sql(f"CREATE TABLE IF NOT EXISTS {_nome_bronze(config, fonte)} ({SCHEMA_BRONZE}) USING DELTA")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {config.tabela_sql('controle','arquivos_bronze_v2')} "
              f"({SCHEMA_CONTROLE}) USING DELTA")


def _registrar_arquivo(spark, config, item, data_referencia, run_id):
    destino=config.tabela_sql("controle","arquivos_bronze_v2")
    fonte=item["fonte"]
    linha=("v2",data_referencia,item["lote"],fonte,item["caminho"],
           item["sha256"],int(item["registros"]),datetime.now(timezone.utc),run_id)
    df=spark.createDataFrame([linha],SCHEMA_CONTROLE)
    df.createOrReplaceTempView("_bronze_arquivo_atual")
    spark.sql(f"""MERGE INTO {destino} t USING _bronze_arquivo_atual s
      ON t.cenario=s.cenario AND t.data_referencia=s.data_referencia AND t.arquivo=s.arquivo
      WHEN NOT MATCHED THEN INSERT *""")
    spark.catalog.dropTempView("_bronze_arquivo_atual")


def _merge_arquivo(spark, config, item, registros, data_referencia, run_id):
    """MERGE determinístico preserva linhas duplicadas com índices diferentes."""
    destino=_nome_bronze(config,item["fonte"])
    quando=datetime.now(timezone.utc)
    linhas=[]
    for indice,reg in enumerate(registros,1):
        chave=sha256(f"v2|{data_referencia}|{item['caminho']}|{indice}".encode()).hexdigest()
        payload=json.dumps(reg,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        linhas.append((chave,item["fonte"],item["lote"],item["caminho"],indice,
                       payload,item["sha256"],data_referencia,quando,run_id))
    if not linhas:
        return
    df=spark.createDataFrame(linhas,SCHEMA_BRONZE)
    df.createOrReplaceTempView("_bronze_linhas_atuais")
    spark.sql(f"""MERGE INTO {destino} t USING _bronze_linhas_atuais s
       ON t.id_registro=s.id_registro
       WHEN NOT MATCHED THEN INSERT *""")
    spark.catalog.dropTempView("_bronze_linhas_atuais")


def executar_bronze_v2(spark, config, lote, run_id):
    """Um lote por execução; falha preserva possibilidade de retomada."""
    validar_lote(lote)
    if config.ambiente!="dev" or config.modo!="incremental" or not config.data_referencia:
        raise ValueError("Bronze V2 restrita a dev/incremental com data_referencia")
    raiz=f"/Volumes/{config.catalogo}/{config.schema('landing')}/arquivos"
    if config.caminho_entrada!=raiz:
        raise ValueError("Volume de entrada diferente do padrão validado")
    dados,manifest_hash=preparar_lote(raiz,config.data_referencia,lote)
    preparar_tabelas(spark,config)
    controle=config.tabela_sql("controle","arquivos_bronze_v2")
    # Fonte de controle serve de evidência, não de condição para pular a
    # gravação. MERGE reexecutado repara eventuais interrupções entre escritas.
    resumo={f:0 for f in FONTES}
    for item,registros in dados:
        existentes=spark.sql(f"SELECT DISTINCT arquivo_sha256 FROM {controle} "
                            f"WHERE cenario='v2' AND data_referencia='{config.data_referencia}' "
                            f"AND arquivo='{item['caminho']}'").collect()
        if any(r[0]!=item["sha256"] for r in existentes):
            raise ValueError(f"Arquivo já registrado com hash divergente: {item['caminho']}")
        _merge_arquivo(spark,config,item,registros,config.data_referencia,run_id)
        _registrar_arquivo(spark,config,item,config.data_referencia,run_id)
        resumo[item["fonte"]]+=len(registros)
    # Recontagem isolada por lote, sem colapsar duplicidades intencionais.
    for fonte,total in resumo.items():
        if not total:
            continue
        encontrado=spark.sql(f"SELECT count(*) n FROM {_nome_bronze(config,fonte)} "
            f"WHERE data_referencia='{config.data_referencia}' AND lote='{lote}'").first()[0]
        if encontrado!=total:
            raise ValueError(f"Recontagem Bronze divergente: {fonte}: {encontrado} != {total}")
    resultado={"lote":lote,"registros_por_fonte":resumo,"manifesto_sha256":manifest_hash,
               "arquivos_processados":len(dados),"run_id":run_id}
    print("BRONZE V2: OK",json.dumps(resultado,ensure_ascii=False,sort_keys=True))
    return resultado
