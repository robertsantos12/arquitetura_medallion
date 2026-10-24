"""Parâmetros explícitos e validação antes de acessar dados."""

import re
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

CAMADAS = ("landing", "bronze", "prata", "ouro", "controle")


def validar_identificador(valor: str) -> str:
    if not isinstance(valor, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", valor):
        raise ValueError(f"Identificador inválido: {valor!r}")
    return valor


@dataclass(frozen=True)
class PipelineConfig:
    ambiente: str = "dev"
    catalogo: str = "workspace"
    modo: str = "incremental"
    data_referencia: str | None = None
    batch_id: str = field(default_factory=lambda: str(uuid4()))
    raiz_arquivos: str | None = None

    def __post_init__(self) -> None:
        if self.ambiente not in ("dev", "hml", "prod"):
            raise ValueError("Ambiente deve ser dev, hml ou prod")
        validar_identificador(self.catalogo)
        if self.modo not in ("incremental", "reprocessamento"):
            raise ValueError("Modo deve ser incremental ou reprocessamento")
        if self.data_referencia is not None:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.data_referencia):
                raise ValueError("Data deve seguir YYYY-MM-DD")
            date.fromisoformat(self.data_referencia)
        if self.modo == "reprocessamento" and self.data_referencia is None:
            raise ValueError("Reprocessamento exige data_referencia")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", self.batch_id):
            raise ValueError("batch_id deve ter 1 a 128 letras, números, _ ou -")
        if self.raiz_arquivos is not None:
            if not self.raiz_arquivos.startswith("/Volumes/"):
                raise ValueError("Use um caminho de Unity Catalog em /Volumes/")
            partes = self.raiz_arquivos.split("/")[2:]
            if len(partes) < 3 or any(p in ("", ".", "..") for p in partes):
                raise ValueError("Informe /Volumes/catalogo/schema/volume[/diretorio]")

    def schema(self, camada: str) -> str:
        if camada not in CAMADAS:
            raise ValueError(f"Camada desconhecida: {camada}")
        return f"medallion_{self.ambiente}_{camada}"

    def schema_sql(self, camada: str) -> str:
        return f"`{self.catalogo}`.`{self.schema(camada)}`"

    def tabela_sql(self, camada: str, tabela: str) -> str:
        return f"{self.schema_sql(camada)}.`{validar_identificador(tabela)}`"

    @property
    def caminho_entrada(self) -> str:
        return self.raiz_arquivos or (
            f"/Volumes/{self.catalogo}/{self.schema('landing')}/arquivos"
        )
