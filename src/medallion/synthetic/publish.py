"""Publicação sequencial e retomável da fixture, sem sobrescrever divergências."""

import json
from pathlib import Path

from medallion.observability.audit import serializar, sha256
from medallion.synthetic.contracts import SCHEMA_VERSION
from medallion.synthetic.generator import arquivos_planejados


def publicar(raiz, data_referencia="2026-01-15"):
    """Um escritor por cenário. Manifesto final confirma a completude, não é lock."""
    arquivos = arquivos_planejados(data_referencia)
    pasta = Path(raiz) / "cenarios" / "v1" / data_referencia
    manifesto = {"schema_version": SCHEMA_VERSION, "data_referencia": data_referencia,
                 "ordem_chegada": ["01_inicial", "02_incremental", "03_atrasado"],
                 "arquivos": [{"caminho": p, "sha256": sha256(b), "registros": n,
                               "fonte": f, "lote": l} for p, (b, n, f, l) in sorted(arquivos.items())]}
    plano = {p: b for p, (b, *_) in arquivos.items()}
    plano["manifesto.json"] = serializar(manifesto)
    # Checar divergências antes de qualquer nova escrita. Arquivos parciais
    # idênticos podem ser retomados; não apagar nem substituir dados divergentes.
    for nome, dados in plano.items():
        path = pasta / nome
        if path.exists() and path.read_bytes() != dados:
            raise ValueError(f"Arquivo existente diverge do cenário: {nome}")
    extras = {p.relative_to(pasta).as_posix() for p in pasta.rglob("*") if p.is_file()} - set(plano)
    if extras:
        raise ValueError(f"Arquivos não previstos no cenário: {sorted(extras)}")
    novos = 0
    for nome, dados in plano.items():
        path = pasta / nome
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(dados)
            novos += 1
        if path.read_bytes() != dados:
            raise OSError(f"Releitura divergente: {nome}")
    return {"pasta": str(pasta), "novos_arquivos": novos,
            "reutilizados": len(plano)-novos, "manifesto": manifesto,
            "manifesto_sha256": sha256((pasta / "manifesto.json").read_bytes())}


def conferir(raiz, data_referencia):
    """Reconstrói o plano e verifica dados/manifesto, sem escrever."""
    pasta = Path(raiz) / "cenarios" / "v1" / data_referencia
    esperado = arquivos_planejados(data_referencia)
    manifesto = json.loads((pasta / "manifesto.json").read_text())
    assert manifesto["data_referencia"] == data_referencia
    assert manifesto["schema_version"] == SCHEMA_VERSION
    observados = []
    for nome, (dados, n, fonte, lote) in sorted(esperado.items()):
        actual = (pasta / nome).read_bytes()
        if actual != dados:
            raise ValueError(f"Dados divergentes: {nome}")
        observados.append({"caminho": nome, "sha256": sha256(actual), "registros": n,
                           "fonte": fonte, "lote": lote})
    if manifesto["arquivos"] != observados:
        raise ValueError("Manifesto divergente")
    return observados
