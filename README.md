# NovaRota — Data Product Lakehouse

Desafio técnico de Engenharia de Dados Sênior em Databricks e Delta Lake.
Construção incremental: cada etapa passa por testes locais e validação no workspace.

## Situação

- Etapa 1 validada pelo responsável no Databricks: Delta, MERGE, releitura e repetição sem duplicidade para a chave de teste.
- Etapa 2 validada nos exports recebidos: pacote Python, configuração, logs e cinco schemas dev.
- Etapa 2B implementada: eventos Delta e evidências em Volume; integração aguarda execução de 02/03.
- Dados sintéticos, Bronze, Prata/SCD2, Ouro e SQL analítico ainda não implementados.

## Executar a etapa 2 no Databricks

1. Na pasta Git, selecione `chore/estrutura-inicial` e faça Pull.
2. Abra `notebooks/01_preparar_projeto.ipynb` e execute todas as células.
3. Mantenha o widget `catalogo` como `workspace`. Os demais parâmetros podem ficar no padrão.
4. Espere `ESTRUTURA DO PROJETO: OK` e a lista de cinco schemas.

O notebook encontra a raiz do repositório a partir do diretório atual, adiciona `src` ao caminho de importação e chama o pacote. Não exige instalação de PySpark nem acesso à internet. Se o diretório atual não apontar para a pasta Git, ajuste-o conforme a mensagem de erro.

O bootstrap cria somente `workspace.medallion_dev_{landing,bronze,prata,ouro,controle}` com `CREATE SCHEMA IF NOT EXISTS` e verifica acesso aos schemas. Pode ser repetido. Uma falha é registrada e propagada; os schemas criados antes dela permanecem disponíveis. A etapa não cria tabelas nem volumes, não concede permissões e não insere dados.

## Testes locais

Python 3.10 ou superior. Na raiz do repositório:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Os testes desta entrega não exigem dependências externas. Cobrem configuração, datas de reprocessamento, isolamento de nomes, bloqueio do bootstrap em produção e propagação de erro. Ainda não existem testes de transformação Spark; serão adicionados junto das transformações. Para instalação como pacote, use `python -m pip install -e .` em um ambiente com setuptools disponível.

## Organização atual

| Caminho | Responsabilidade |
| --- | --- |
| `src/medallion/config/` | Parâmetros e validação sem depender de Spark |
| `src/medallion/observability/` | Logs JSON em UTC com contexto de execução |
| `src/medallion/bootstrap.py` | Preparação dos schemas dev |
| `notebooks/` | Execução e diagnóstico no Databricks |
| `tests/` | Testes automatizados |
| `docs/` | Arquitetura, decisões e evidências |

Módulos de ingestão, qualidade, Prata e Ouro serão criados com suas implementações, evitando diretórios sem função nesta entrega.

## Parâmetros

| Parâmetro | Padrão | Uso |
| --- | --- | --- |
| `ambiente` | `dev` | Configuração aceita dev/hml/prod; bootstrap libera apenas dev |
| `catalogo` | `workspace` | Catálogo existente no Unity Catalog |
| `modo` | `incremental` | Alternativa: `reprocessamento` |
| `data_referencia` | sem valor | YYYY-MM-DD; obrigatória em reprocessamento |
| `batch_id` | UUID novo | Pode ser informado para correlacionar uma retentativa |
| `raiz_arquivos` | `/Volumes/<catalogo>/medallion_dev_landing/arquivos` | Caminho planejado; volume e acesso ainda não validados |

Modo, data e path são parâmetros preparados para o futuro pipeline: ainda não disparam cargas. O batch_id permite correlação de logs; sozinho não garante idempotência de ingestão.

## Fluxo Git

O trabalho atual está em `chore/estrutura-inicial`. Após validação, a integração proposta é PR para `develop`; novas funcionalidades partem de `develop` e retornam por PR. A integração de `develop` em `main` ocorre após revisão e evidências. Nenhum merge foi feito nesta entrega. Commits seguem Conventional Commits.

## Próximas etapas

1. Executar 02_validar_rastreabilidade e 03_reler_evidencias para validar Delta + Volume.
2. Definir contratos, gerar massa sintética determinística e validar arquivos no Volume.
3. Implementar Bronze incremental, metadados e preservação de schema.
4. Implementar qualidade, quarentena, MERGE e SCD2 na Prata, com testes de transformação.
5. Implementar Ouro, SQL avançado, testes ponta a ponta e evidências.

Veja `docs/architecture.md`, `docs/decisions.md` e `docs/evidencias.md`.

## Evidências padronizadas

Os outputs dos notebooks devem acompanhar os commits de validação. O repositório inclui `.databricks/commit_outputs`; é necessário habilitar o recurso no workspace e verificar o primeiro envio com resultados reais. Consulte `docs/preservacao_execucoes.md` antes de executar as próximas etapas. Esta configuração preserva checkpoints feitos por commit, e não todas as tentativas automaticamente.

A investigação de 24/10/2026 confirmou outputs vazios no GitHub apesar de resultados visíveis no workspace. Antes de continuar, consulte `docs/rastreabilidade_execucoes.md` e preserve os notebooks por exportação com outputs. A primeira implementação de registro Delta/Volume está disponível e aguarda teste no workspace; veja docs/rastreabilidade_implementacao.md.

## Próxima execução — etapa 2B

Faça Pull e execute `notebooks/02_validar_rastreabilidade.ipynb`. Ele registra duas tentativas de sucesso e uma falha controlada, preservadas separadamente. Depois use os três run_ids no notebook `03_reler_evidencias.ipynb`, em nova sessão Python. Instruções: `docs/rastreabilidade_implementacao.md`. Foram aprovados 17 testes locais; as integrações Delta e Volume ainda precisam dessa execução.
