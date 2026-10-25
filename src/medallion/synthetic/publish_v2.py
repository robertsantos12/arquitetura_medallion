"""Publica V2 em namespace próprio; V1 permanece intacta."""
import json
from pathlib import Path
from medallion.observability.audit import serializar, sha256
from medallion.synthetic.contracts import CONTRACTS
from medallion.synthetic.generator_v2 import arquivos_planejados_v2

def publicar_v2(raiz, data_referencia="2026-01-15"):
    arquivos = arquivos_planejados_v2(data_referencia)
    pasta = Path(raiz)/"cenarios"/"v2"/data_referencia
    manifesto = {"schema_version": 1, "cenario":"v2", "data_referencia":data_referencia,
        "ordem_chegada":["01_inicial","02_incremental","03_atrasado"],
        "arquivos":[{"caminho":p,"sha256":sha256(b),"registros":n,"fonte":f,"lote":l}
                    for p,(b,n,f,l) in sorted(arquivos.items())]}
    plano = {p:b for p,(b,*_) in arquivos.items()}
    plano["manifesto.json"] = serializar(manifesto)
    for nome,dados in plano.items():
        alvo=pasta/nome
        if alvo.exists() and alvo.read_bytes()!=dados:
            raise ValueError(f"Arquivo existente diverge do cenário V2: {nome}")
    extras={p.relative_to(pasta).as_posix() for p in pasta.rglob("*") if p.is_file()}-set(plano)
    if extras:
        raise ValueError(f"Arquivos não previstos: {sorted(extras)}")
    novos=0
    for nome,dados in plano.items():
        alvo=pasta/nome
        if not alvo.exists():
            alvo.parent.mkdir(parents=True,exist_ok=True)
            alvo.write_bytes(dados)
            novos+=1
        if alvo.read_bytes()!=dados:
            raise OSError(f"Releitura divergente: {nome}")
    return {"pasta":str(pasta),"novos_arquivos":novos,"reutilizados":len(plano)-novos,
            "manifesto":manifesto,"manifesto_sha256":sha256((pasta/"manifesto.json").read_bytes())}

def conferir_v2(raiz, data_referencia):
    pasta=Path(raiz)/"cenarios"/"v2"/data_referencia
    esperado=arquivos_planejados_v2(data_referencia)
    manifesto=json.loads((pasta/"manifesto.json").read_text())
    if manifesto["data_referencia"]!=data_referencia or manifesto["cenario"]!="v2":
        raise ValueError("Metadados do manifesto V2 divergentes")
    observados=[]
    for nome,(dados,n,fonte,lote) in sorted(esperado.items()):
        actual=(pasta/nome).read_bytes()
        if actual!=dados:
            raise ValueError(f"Dados divergentes: {nome}")
        observados.append({"caminho":nome,"sha256":sha256(actual),
                           "registros":n,"fonte":fonte,"lote":lote})
    if manifesto["arquivos"]!=observados:
        raise ValueError("Manifesto V2 divergente")
    return observados
