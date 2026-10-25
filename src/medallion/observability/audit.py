"""Registro por tentativa, independente da saída visual do notebook.

Cada arquivo é escrito sequencialmente uma vez. Delta e Volume não formam uma
transação única: erro de gravação interrompe a execução e exige reconciliação.
"""

import hashlib
import json
import platform
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from medallion.config import PipelineConfig
from medallion.config.settings import validar_identificador


class AuditPersistenceError(RuntimeError):
    """Não foi possível confirmar a persistência da evidência."""


def serializar(valor) -> bytes:
    return (json.dumps(valor, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def capturar_fontes(raiz: Path) -> dict[str, str]:
    """Snapshot dos módulos e pyproject lidos no início, sem credenciais."""
    raiz = Path(raiz)
    paths = sorted((raiz / "src" / "medallion").rglob("*.py"))
    if not paths or not (raiz / "pyproject.toml").is_file():
        raise ValueError("Raiz do pacote não encontrada")
    paths.append(raiz / "pyproject.toml")
    return {p.relative_to(raiz).as_posix(): p.read_text(encoding="utf-8") for p in paths}


class AuditRun:
    """Um objeto por tentativa. O sink deve implementar append(evento, arquivo, hash)."""

    def __init__(self, raiz, sink, config: PipelineConfig, etapa: str,
                 fontes: dict[str, str], runtime: dict | None = None):
        validar_identificador(etapa)
        if not fontes:
            raise ValueError("Snapshot de código obrigatório")
        self.run_id = str(uuid4())
        self.pasta = Path(raiz) / self.run_id
        self.sink = sink
        self.fontes = dict(fontes)
        self.contexto = {
            "schema_version": 1, "run_id": self.run_id, "etapa": etapa,
            "parametros": asdict(config), "batch_id": config.batch_id,
            "codigo_sha256": sha256(serializar(self.fontes)),
            "runtime": {"python": platform.python_version(), **(runtime or {})},
        }
        self.arquivos = []
        self.sequencia = 0
        self.checks = 0
        self.iniciado = False
        self.finalizado = False
        self.falha_persistencia = False

    def _gravar(self, nome: str, valor) -> tuple[str, str]:
        path = self.pasta / nome
        dados = serializar(valor)
        if path.exists():
            raise FileExistsError(f"Não sobrescrever evidência: {path}")
        path.write_bytes(dados)
        if path.read_bytes() != dados:
            raise OSError(f"Releitura divergente: {path}")
        digest = sha256(dados)
        self.arquivos.append({"nome": nome, "sha256": digest})
        return str(path), digest

    def _evento(self, status: str, detalhes: dict) -> None:
        if self.finalizado or self.falha_persistencia:
            raise AuditPersistenceError("Tentativa encerrada ou persistência comprometida")
        self.sequencia += 1
        evento = {
            **self.contexto, "event_id": f"{self.run_id}:{self.sequencia:04d}",
            "sequencia": self.sequencia, "status": status,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "detalhes": detalhes, "arquivos_anteriores": list(self.arquivos),
        }
        try:
            arquivo, digest = self._gravar(f"{self.sequencia:04d}_{status}.json", evento)
            self.sink.append(evento, arquivo, digest)
        except Exception as exc:
            self.falha_persistencia = True
            raise AuditPersistenceError(f"Falha ao persistir {status}; run_id={self.run_id}") from exc
        print(json.dumps({"run_id": self.run_id, "status": status,
                          "arquivo": arquivo}, ensure_ascii=False))

    def verificar(self, nome: str, observado, esperado) -> None:
        if not self.iniciado or self.finalizado:
            raise RuntimeError("Verificação fora de uma execução ativa")
        passou = observado == esperado
        self._evento("VERIFICACAO", {"nome": nome, "observado": observado,
                                     "esperado": esperado, "passou": passou})
        if not passou:
            raise AssertionError(f"Verificação falhou: {nome}")
        self.checks += 1

    def executar(self, funcao) -> str:
        if self.iniciado:
            raise RuntimeError("Crie outra tentativa para repetir a execução")
        self.iniciado = True
        try:
            self.pasta.mkdir(parents=True, exist_ok=False)
            self._gravar("fontes.json", self.fontes)
            self._gravar("contexto.json", self.contexto)
        except Exception as exc:
            self.falha_persistencia = True
            raise AuditPersistenceError("Falha ao iniciar arquivo de evidências") from exc
        self._evento("INICIADA", {})
        try:
            funcao(self)
            if not self.checks:
                raise ValueError("Execução sem verificações não pode ser aprovada")
        except AuditPersistenceError:
            raise
        except Exception as erro_original:
            detalhes = {"tipo": type(erro_original).__name__, "mensagem": str(erro_original),
                        "traceback": traceback.format_exc()}
            try:
                self._evento("FALHOU", detalhes)
            except AuditPersistenceError as erro_arquivo:
                raise AuditPersistenceError(
                    f"Processamento e arquivamento falharam: {erro_arquivo}"
                ) from erro_original
            self.finalizado = True
            raise
        self._evento("SUCESSO", {"verificacoes_aprovadas": self.checks})
        self.finalizado = True
        return self.run_id


def verificar_arquivos(registros: list[dict]) -> dict:
    """Verifica registros relidos do destino, inclusive checksums e sequência."""
    if not registros:
        raise ValueError("Nenhum evento encontrado")
    eventos = []
    for registro in registros:
        path = Path(registro["arquivo"])
        dados = path.read_bytes()
        if sha256(dados) != registro["arquivo_sha256"]:
            raise ValueError(f"Hash divergente: {path.name}")
        evento = json.loads(dados)
        if evento != json.loads(registro["payload_json"]):
            raise ValueError("Conteúdo do Volume diverge do registro Delta")
        if evento["event_id"] != registro["event_id"]:
            raise ValueError("Identificador de evento divergente")
        for anterior in evento["arquivos_anteriores"]:
            nome = anterior["nome"]
            if Path(nome).name != nome or nome in (".", ".."):
                raise ValueError("Nome de artefato inválido")
            if sha256((path.parent / nome).read_bytes()) != anterior["sha256"]:
                raise ValueError(f"Artefato anterior divergente: {nome}")
        eventos.append(evento)
    eventos.sort(key=lambda e: e["sequencia"])
    ids = {e["run_id"] for e in eventos}
    if len(ids) != 1 or [e["sequencia"] for e in eventos] != list(range(1, len(eventos) + 1)):
        raise ValueError("Eventos misturados, duplicados ou sequência incompleta")
    if eventos[0]["status"] != "INICIADA":
        raise ValueError("Falta evento de início")
    terminais = [e for e in eventos if e["status"] in ("SUCESSO", "FALHOU")]
    if len(terminais) > 1 or (terminais and terminais[0] != eventos[-1]):
        raise ValueError("Conclusão duplicada ou fora de ordem")
    checks = [e for e in eventos if e["status"] == "VERIFICACAO"]
    status = terminais[0]["status"] if terminais else "SEM_CONCLUSAO"
    if status == "SUCESSO" and (not checks or not all(e["detalhes"]["passou"] for e in checks)):
        raise ValueError("Sucesso sem verificações aprovadas")
    return {"run_id": next(iter(ids)), "status": status, "eventos": len(eventos),
            "codigo_sha256": eventos[0]["codigo_sha256"], "hashes_verificados": True}
