# NovaRota — Lakehouse Databricks/Delta

Case sênior com massa fictícia V2 temática de Chaves, Bronze incremental e preparação de Silver/Gold/SQL para homologação.

## Estado real

- 00–05: validados anteriormente pelo operador; exports em docs/evidencias. Massa V2 e schemas Bronze preservados nesta revisão.
- 06–09: implementados; **34 testes locais aprovados**. Integração no Databricks ainda PENDENTE. Não existem outputs Databricks novos nesta entrega.
- Trabalho apenas em `chore/estrutura-inicial`; sem merge em develop/main.

## Homologar às 11h de domingo

Siga [docs/homologacao_domingo.md](docs/homologacao_domingo.md), um notebook por vez. Faça Pull e use Python novo. **Não regenere a massa nem reexecute 00–05.**

| Notebook | Parâmetros |
|---|---|
| 06_processar_silver | catalogo=workspace, data_referencia=2026-01-15, modo=incremental; guardar SNAPSHOT_SILVER |
| 07_construir_gold | mesmos catálogo/data, snapshot_silver do 06, data_corte=2026-05-31; guardar SNAPSHOT_GOLD |
| 08_analises_sql | mesmos catálogo/data e snapshot_gold do 07 |
| 09_validar_pipeline | mesmos catálogo/data, IDs Silver/Gold, mesmo corte do 07 |

Execute só o primeiro CMD para mostrar widgets, preencha e execute os demais. Após cada etapa exporte IPYNB com outputs, confira e faça commit de validação. Preserve falhas e pare; não apague tabelas.

## Código e testes

Transformações em src/medallion/{quality,silver,gold}; persistência, SQL e execução em src/medallion/pipeline; validador Bronze em src/medallion/bronze/validate.py. SQL em sql/. Notebooks são adaptadores finos. Sem dependências externas para testes puros:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Os testes cobrem fixture V1/V2 serializada, SCD2 atrasado, conflitos, qualidade, recusas, estornos, corte temporal, oráculo V1=R$2.270, determinismo e protocolo de snapshots com dublê. O dublê não substitui Spark/Delta. SQL/EXPLAIN precisam do Databricks.

## Decisões e limites

Silver/Gold são snapshots Delta imutáveis: MERGE insert-only e marcador de completude. Cada consulta exige snapshot_id. Não somar snapshots. Reprocessamento recompõe o cenário, preservando versões anteriores. Processamento no driver é decisão do case pequeno, não desenho de escala; migração distribuída está no backlog.

Contratos financeiros e temporais: [docs/contrato_homologacao.md](docs/contrato_homologacao.md). Grãos, governança e operação: [docs/homologacao_domingo.md](docs/homologacao_domingo.md). Bloqueios e limitações: [docs/backlog_v2.md](docs/backlog_v2.md). Revisão de baseline: [docs/revisao_homologacao.md](docs/revisao_homologacao.md).

O formato final exigido no PDF é repositório privado ou pacote compactado. Preparação da entrega final e validação real seguem pendentes; não foi alterada a visibilidade do repositório.
