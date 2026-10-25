# Evidência — geração sintética V2 (24/10/2026)

Origem: export do Databricks fornecido pelo responsável, `04_gerar_dados_sinteticos_v2(1).ipynb`. Os outputs desse export foram incorporados ao notebook versionado em `notebooks/04_gerar_dados_sinteticos_v2.ipynb`. Registro baseado no export recebido, **não** em consulta independente ao Databricks.

- Branch: `chore/estrutura-inicial`
- Catálogo: `workspace`
- Data de referência: `2026-01-15`
- Resultado: `DADOS SINTÉTICOS V2: OK`
- Clientes distintos: **21** (18 personagens adicionais + clientes de contrato original)
- Transações: **12.158**
- Arquivos novos reportados: **138**
- Caminho: `/Volumes/workspace/medallion_dev_landing/arquivos/cenarios/v2/2026-01-15`
- SHA256 do manifesto: `480bcccda11f61d9e29f6a9dd56a0f106b7fd05ad32903b0c768428e3e7113a9`
- RUN_ID: `45599d53-5189-4644-b92a-703eb3b5154d`
- Resultado da auditoria: `SUCESSO`, **7** eventos, `hashes_verificados=True`
- Hash de fontes reportado: `7046a5d4f8eab3cc0795e8d54322a5f3b413241aa24ffeee67a26c02c3b0b7a7`

## Resumo por lote

| Lote | clientes_cdc | contas_cdc | cartoes_cdc | transacoes | eventos_risco | estornos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 01_inicial | 22 | 22 | 22 | 6080 | 1 | 1 |
| 02_incremental | 1 | 1 | 2 | 4560 | 3 | 2 |
| 03_atrasado | 1 | 0 | 0 | 1518 | 0 | 1 |

## Escopo da validação

Os outputs evidenciam publicação e releitura dos arquivos, seis fontes, manifesto, teste interno de repetição sem gravações adicionais e auditoria do executor. A contagem de clientes distintos não deve ser confundida com o número de linhas CDC (que contém versões e duplicidades intencionais).

**Não validado nesta evidência:** ingestão Bronze, tratamento Silver, SCD2, Gold, métricas de negócios e execução ponta a ponta. Repetição em uma execução independente e testes locais adicionais ainda podem fortalecer a comprovação.
