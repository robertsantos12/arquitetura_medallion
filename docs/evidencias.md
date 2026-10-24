# Evidências de validação

## Etapa 1 — Delta

Execução realizada no Databricks pelo responsável pelo projeto e confirmada na conversa de 24/10/2026. Saída informada:

```text
VALIDAÇÃO DELTA: OK
Catálogo: workspace
Schema: medallion_dev_setup
Formato: delta
MERGE e releitura: OK
Repetição sem duplicidade para id=1: OK
```

Escopo: tabela de diagnóstico com chave controlada; não comprova idempotência de ingestão nem transformações futuras. A confirmação textual não substitui um log ou exportação de células executadas como evidência final da entrega.

## Etapa 2 — Estrutura

Validação no Databricks pendente. Executar `notebooks/01_preparar_projeto.ipynb` e registrar a saída final.

Verificação local em 24/10/2026: `PYTHONPATH=src python3 -m unittest discover -s tests -v`, com 7 testes aprovados. Sintaxe das células do notebook e estrutura do pyproject.toml também verificadas. Os testes locais verificam apenas as regras Python e a propagação de falhas; a integração com o ambiente depende da execução no Databricks.

## Preservação dos outputs

Política preparada em `.databricks/commit_outputs`, com instruções em `docs/preservacao_execucoes.md`. Habilitação no workspace e primeiro commit com outputs reais ainda pendentes. Reexecutar 00 e 01 e versionar cada validação antes de avançar. O registro textual acima continua sendo confirmação informada pelo responsável, não um output capturado automaticamente.
