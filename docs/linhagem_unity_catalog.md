# Linhagem Bronze → Silver → Gold

## Causa e solução da entrega

Os processamentos 06/07 usam collect, regras Python e createDataFrame. Essas fronteiras não preservam o plano Spark que liga leitura e escrita; a captura automática não reconstrói todas as dependências do código Python. PK, comentários e tags não criam arestas de linhagem.

O notebook 12 usa o mecanismo oficial External Metadata/External Lineage para acrescentar relações declaradas, com um nó de transformação Python entre ativos UC. O recurso é compatível com a modelagem documentada de conexão entre duas tabelas UC. Não cria tabela fictícia nem usa MERGE vazio, joins artificiais ou escritas para produzir evidência de execução inexistente. Os nós representam transformações reais da implementação atual; system_type=DATABRICKS, nr_tipo=declarada. Não são captura runtime retroativa nem entidade externa ao workspace.

Grafo esperado: tabela Gold ← transformação Python declarada ← tabela Silver ← transformação Python declarada ← tabela Bronze. São 15 nós intermediários (sete destinos Silver incluindo quarentena e oito Gold). Dependências incluem dimensões temporais, estornos e risco conforme o código. Relações são no nível de tabela, não há promessa de linhagem de cada coluna ou de cada snapshot. O modelo representa dependências da versão do pipeline, não cada tentativa. A trilha de run_id/snapshot/hash continua nas evidências originais.

## Aplicação e conferência

Faça Pull, use sessão Python nova, abra 12_registrar_linhagem. Execute CMD 1, catalogo=workspace, depois CMDs 2 e 3. Usa WorkspaceClient com autenticação nativa; não inserir tokens. Requer SDK com api_client, API de external lineage habilitada e privilégios: CREATE EXTERNAL METADATA no metastore, MODIFY nos objetos externos e origens UC, SELECT nos destinos UC. Execução local não confirmou disponibilidade dessas capacidades no workspace Free Edition.

Só objetos ausentes são criados. Nomes são derivados do destino; metadado preexistente incompatível bloqueia, sem overwrite. Arestas são listadas com paginação antes/depois da criação e duplicatas existentes bloqueiam. Não há atomicidade entre APIs: preservar output e retomar se houver falha. Não oculta erros nem declara sucesso por criação parcial. Permissões e compatibilidade da API precisam ser validadas pelo operador.

Após LINHAGEM DECLARADA: OK, abrir Catalog → workspace → medallion_dev_ouro → gold_fato_transacao → Lineage e expandir upstream, pelos nós nr_python_*, até Silver e Bronze. Repetir para um agregado e uma dimensão. Necessário BROWSE/visibilidade apropriada dos ativos; atualização do grafo pode não ser imediata. Enviar export e captura para comprovar o resultado visual. External lineage não aparece em system.access.table_lineage/column_lineage; essas tabelas não são o critério de aceite deste complemento.

## Estado e evolução V2

IMPLEMENTADO: mapa de dependências e criação/releitura pela API. TESTADO LOCALMENTE: cobertura/ausência de ciclos, identidade estável e repetição idempotente com API dublê (três testes), mais sintaxe de módulos/notebooks. PENDENTE: API real, privilégios e grafo visual. Não houve alteração dos registros, writers 06/07 ou snapshots existentes.

V2: migrar transformações para Spark DataFrames/SQL mantendo o plano de leitura até MERGE, validar captura nativa em nível de tabela/coluna e regressão financeira num destino novo controlado. Não reprocessar os snapshots antigos apenas para preencher o grafo. Antes de promover nova versão, atualizar o mapa declarado de forma versionada e revisar conexões obsoletas; exclusões de metadados não são automáticas.

Fontes oficiais:
- https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage
- https://docs.databricks.com/aws/en/data-governance/unity-catalog/external-lineage
- https://docs.databricks.com/api/uc-external-lineage/v1/create-external-lineage-relationship
