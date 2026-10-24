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

Em 24/10/2026, os prints enviados mostram a opção included e a conclusão bem-sucedida do notebook 00 no workspace. O commit 8eb90b2a78304b7661146e3a123cf948ed43ca4b contém 00 e 01 com outputs vazios; os hashes Git dos bytes foram conferidos. A preservação remota das execuções continua pendente. Exportar as saídas atuais antes de reexecutar ou sincronizar. Ver docs/rastreabilidade_execucoes.md. Os prints foram apenas inspecionados na conversa, não adicionados ao repositório.
