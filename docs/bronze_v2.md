# Etapa 05 — Bronze incremental V2

## Origem e tabelas

Branch de trabalho: `chore/estrutura-inicial`. Arquivos publicados pela etapa 04: `/Volumes/workspace/medallion_dev_landing/arquivos/cenarios/v2/2026-01-15`. São seis fontes, preservadas em seis tabelas Delta no schema `workspace.medallion_dev_bronze`:

- `raw_clientes_cdc`
- `raw_contas_cdc`
- `raw_cartoes_cdc`
- `raw_transacoes`
- `raw_eventos_risco`
- `raw_estornos`

A tabela `workspace.medallion_dev_controle.arquivos_bronze_v2` registra arquivos processados, lotes, SHA256, número de linhas, execução e horário. Esta fase preserva dados inválidos intencionais, duplicatas e evolução das colunas dentro de `payload_json`. **Não aplica qualidade, SCD2 ou regras financeiras**, que pertencem à Prata.

## Idempotência, recuperação e limitações

A execução valida o manifesto V2, SHA256 e contagem de cada arquivo **antes** de iniciar gravação do lote. A chave de cada linha é SHA256 de `v2|data_referencia|arquivo_relativo|linha_1_based`. Cada arquivo passa por MERGE INTO: linhas já presentes não são adicionadas, mas duplicidades legítimas em posições distintas permanecem. Depois da gravação das linhas, o controle de arquivo é registrado também com MERGE; uma interrupção entre ambas as operações pode ser recuperada repetindo o mesmo lote (MERGE da Bronze precede novamente o controle). Tabela de controle é evidência, não mecanismo para pular uma correção. Hash divergente de arquivo já conhecido interrompe a execução.

Os MERGEs por arquivo/tabela **não formam uma transação Delta única entre tabelas**. A estratégia é **retomada idempotente, não atomicidade multi-tabela**. Exige apenas um escritor por cenário/lote e não limpa dados antigos. Os arquivos CSV são lidos pela biblioteca padrão no driver, adequados ao pequeno volume sintético do desafio; em ambiente de escala real, recomenda-se Auto Loader/Structured Streaming e checkpoint com esquema governado. As métricas são recontadas por fonte e lote. A Bronze não deduplica transações por id_transacao, propositalmente.

## Roteiro de execução

1. Faça Pull de `chore/estrutura-inicial` no Databricks.
2. Abra `notebooks/05_ingerir_bronze_v2.ipynb` e defina `catalogo=workspace`, `data_referencia=2026-01-15`, `lote=01_inicial`.
3. Execute células até o final, registre as seis fontes e o resultado `BRONZE V2: OK`.
4. Repita **01_inicial** e confirme contagens invariáveis.
5. Troque para `02_incremental` e execute; depois `03_atrasado`, sem paralelismo.
6. Confira `raw_transacoes` por lote: 6080, 4560, 1518; total 12158.
7. Exporte o notebook **com outputs** e envie para revisão antes da Silver.

## Evidência / status

Código e notebook entregues para validação do responsável no Databricks. A integração real, permissão de CREATE TABLE, MERGE e contagens finais **ainda não estão comprovadas**.


## Atualização — preparação para homologação

Atualização de status: os quatro exports Bronze foram enviados pelo operador e arquivados antes desta revisão. Validador somente leitura validate.py compara manifesto, controle e payload/SHA/linha. Limitações físicas de metadados e melhorias de escrita permanecem explícitas em backlog_v2.md; nenhuma migração da Bronze foi executada.
