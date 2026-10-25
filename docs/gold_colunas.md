# Dicionário Gold — colunas, PK e tags

Implementado para aplicação no notebook 11; pendente de execução no Databricks. PK usa o grão natural incluindo snapshot_id, não apenas o ID da entidade. Dimensões SCD2 incluem vigente_desde. row_key segue como chave técnica de MERGE.

## gold_fato_transacao

PK: snapshot_id, id_transacao

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|id_transacao|Identificador de negócio da tentativa de pagamento, aprovada, recusada ou cancelada. Componente da chave primária composta.|pk|
|id_cartao|Identificador do cartão utilizado na tentativa de pagamento.|atributo|
|data_transacao|Instante UTC da tentativa. Define competência mensal e vínculo cadastral temporal.|atributo|
|valor|Valor solicitado na tentativa em BRL, inclusive recusas. Não somar como gasto efetivo.|atributo|
|mcc|Código da categoria comercial do estabelecimento na origem.|atributo|
|estabelecimento|Nome comercial simulado do estabelecimento.|atributo|
|canal|Canal de captura informado na origem, como POS.|atributo|
|pais|Código do país informado na transação.|atributo|
|moeda|Moeda da tentativa; nesta entrega somente BRL é aceita na Silver.|atributo|
|status_transacao|APROVADA gera gasto; RECUSADA e CANCELADA são tentativas válidas com gasto zero.|atributo|
|motivo_recusa|Motivo textual informado na origem para recusa; pode ser nulo e não comprova saldo real.|atributo|
|id_conta|Identificador da conta do cliente.|atributo|
|id_cliente|Identificador do cliente fictício. Não representa CPF.|atributo|
|nome|Nome do personagem/cliente fictício na versão cadastral aplicável.|atributo|
|cidade|Cidade da versão cadastral aplicável. Na fato, vigente na data da transação.|atributo|
|segmento|Segmento cadastral do cliente. Na fato, vigente na data da transação.|atributo|
|cliente_versao|Chave da versão cadastral do cliente vigente na transação. Join com row_key da dimensão e mesmo snapshot Gold.|referencia_temporal|
|conta_versao|Chave da versão da conta vigente na transação. Join com row_key da dimensão e mesmo snapshot Gold.|referencia_temporal|
|cartao_versao|Chave da versão do cartão vigente na transação. Join com row_key da dimensão e mesmo snapshot Gold.|referencia_temporal|
|payload_json|Conteúdo semântico preservado da origem, incluindo campos extras; pode conter tokens e nomes fictícios.|atributo|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|valor_bruto|Gasto aprovado em BRL antes dos estornos. Zero para recusas/cancelamentos.|atributo|
|valor_estornado|Soma de estornos válidos conhecidos até o corte, em BRL. No mensal, atribuída ao mês da compra original.|atributo|
|valor_liquido|Gasto bruto menos estornos válidos até o corte, em BRL. Chargeback não é descontado novamente.|atributo|
|data_corte|Último dia inclusivo UTC dos eventos considerados. Não garante disponibilidade histórica por chegada.|atributo|
|mes|Primeiro dia do mês de competência da transação em UTC; estornos são atribuídos à compra original.|atributo|
|id_estabelecimento|Identificador derivado do nome do estabelecimento nesta fixture, sem cadastro externo.|atributo|

## gold_cliente_mes

PK: snapshot_id, id_cliente, mes

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|id_cliente|Identificador do cliente fictício. Não representa CPF. Componente da chave primária composta.|pk|
|mes|Primeiro dia do mês de competência da transação em UTC; estornos são atribuídos à compra original. Componente da chave primária composta.|pk|
|tentativas|Quantidade de tentativas válidas, incluindo aprovadas, recusadas e canceladas.|atributo|
|aprovadas|Quantidade de tentativas com status APROVADA, incluindo compras posteriormente estornadas.|atributo|
|recusadas|Quantidade de tentativas RECUSADA, sem gasto efetivo.|atributo|
|canceladas|Quantidade de tentativas CANCELADA, sem gasto efetivo.|atributo|
|valor_bruto|Gasto aprovado em BRL antes dos estornos. Zero para recusas/cancelamentos.|atributo|
|valor_estornado|Soma de estornos válidos conhecidos até o corte, em BRL. No mensal, atribuída ao mês da compra original.|atributo|
|valor_liquido|Gasto bruto menos estornos válidos até o corte, em BRL. Chargeback não é descontado novamente.|atributo|

## gold_indicadores_risco

PK: snapshot_id, id_transacao

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|id_transacao|Identificador de negócio da tentativa de pagamento, aprovada, recusada ou cancelada. Componente da chave primária composta.|pk|
|id_cliente|Identificador do cliente fictício. Não representa CPF.|atributo|
|eventos|Quantidade de eventos de risco válidos da transação até o corte; zero quando não há eventos.|atributo|
|chargebacks|Quantidade de eventos CHARGEBACK até o corte, sem novo abatimento financeiro.|atributo|
|valor_estornado|Soma de estornos válidos conhecidos até o corte, em BRL. No mensal, atribuída ao mês da compra original.|atributo|
|data_corte|Último dia inclusivo UTC dos eventos considerados. Não garante disponibilidade histórica por chegada.|atributo|

## gold_features_cliente

PK: snapshot_id, id_cliente, data_corte

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|id_cliente|Identificador do cliente fictício. Não representa CPF. Componente da chave primária composta.|pk|
|data_corte|Último dia inclusivo UTC dos eventos considerados. Não garante disponibilidade histórica por chegada. Componente da chave primária composta.|pk|
|tentativas|Quantidade de tentativas válidas, incluindo aprovadas, recusadas e canceladas.|atributo|
|aprovadas|Quantidade de tentativas com status APROVADA, incluindo compras posteriormente estornadas.|atributo|
|recusadas|Quantidade de tentativas RECUSADA, sem gasto efetivo.|atributo|
|valor_liquido|Gasto bruto menos estornos válidos até o corte, em BRL. Chargeback não é descontado novamente.|atributo|
|dias_desde_ultima_compra|Dias entre o corte e a última tentativa APROVADA; pode incluir compra depois estornada. Nulo se não há aprovação.|atributo|

## gold_dim_cliente

PK: snapshot_id, id_cliente, vigente_desde

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|id_cliente|Identificador do cliente fictício. Não representa CPF. Componente da chave primária composta.|pk|
|cpf|Token sintético do documento do cliente, sem CPF real nem validação de dígitos.|atributo|
|nome|Nome do personagem/cliente fictício na versão cadastral aplicável.|atributo|
|cidade|Cidade da versão cadastral aplicável. Na fato, vigente na data da transação.|atributo|
|estado|Sigla da unidade federativa do cadastro fictício.|atributo|
|renda|Renda declarada simulada do cliente, em BRL. Não é renda inferida do consumo.|atributo|
|segmento|Segmento cadastral do cliente. Na fato, vigente na data da transação.|atributo|
|data_atualizacao|Instante UTC de vigência da alteração cadastral na origem CDC.|atributo|
|operacao|Operação CDC: I inclusão, U atualização, D tombstone; D não apaga o histórico.|atributo|
|vigente_desde|Início inclusivo UTC da versão histórica SCD2. Componente da chave primária composta.|pk|
|vigente_ate|Fim exclusivo UTC da versão SCD2; nulo indica versão sem término conhecido.|atributo|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|payload_json|Conteúdo semântico preservado da origem, incluindo campos extras; pode conter tokens e nomes fictícios.|atributo|

## gold_dim_conta

PK: snapshot_id, id_conta, vigente_desde

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|id_conta|Identificador da conta do cliente. Componente da chave primária composta.|pk|
|id_cliente|Identificador do cliente fictício. Não representa CPF.|atributo|
|tipo_conta|Modalidade da conta conforme cadastro de origem.|atributo|
|status_conta|Estado cadastral da conta: ATIVA, ENCERRADA ou BLOQUEADA.|atributo|
|data_abertura|Data declarada de abertura da conta.|atributo|
|data_atualizacao|Instante UTC de vigência da alteração cadastral na origem CDC.|atributo|
|operacao|Operação CDC: I inclusão, U atualização, D tombstone; D não apaga o histórico.|atributo|
|vigente_desde|Início inclusivo UTC da versão histórica SCD2. Componente da chave primária composta.|pk|
|vigente_ate|Fim exclusivo UTC da versão SCD2; nulo indica versão sem término conhecido.|atributo|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|payload_json|Conteúdo semântico preservado da origem, incluindo campos extras; pode conter tokens e nomes fictícios.|atributo|

## gold_dim_cartao

PK: snapshot_id, id_cartao, vigente_desde

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|id_cartao|Identificador do cartão utilizado na tentativa de pagamento. Componente da chave primária composta.|pk|
|id_conta|Identificador da conta do cliente.|atributo|
|tipo_cartao|Modalidade do cartão na origem: débito/crédito. Não inferir saldo a partir deste campo.|atributo|
|limite|Limite cadastral simulado em BRL, não saldo disponível.|atributo|
|status_cartao|Estado cadastral: ATIVO, CANCELADO ou BLOQUEADO.|atributo|
|data_atualizacao|Instante UTC de vigência da alteração cadastral na origem CDC.|atributo|
|operacao|Operação CDC: I inclusão, U atualização, D tombstone; D não apaga o histórico.|atributo|
|vigente_desde|Início inclusivo UTC da versão histórica SCD2. Componente da chave primária composta.|pk|
|vigente_ate|Fim exclusivo UTC da versão SCD2; nulo indica versão sem término conhecido.|atributo|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|payload_json|Conteúdo semântico preservado da origem, incluindo campos extras; pode conter tokens e nomes fictícios.|atributo|

## gold_dim_estabelecimento

PK: snapshot_id, id_estabelecimento

|Coluna|Descrição de negócio|Papel|
|---|---|---|
|snapshot_id|Identificador da versão completa dos dados. Filtrar um único snapshot para evitar somar versões. Componente da chave primária composta.|pk|
|row_key|Identificador técnico do registro dentro do snapshot, usado pelo MERGE idempotente.|chave_merge|
|id_estabelecimento|Identificador derivado do nome do estabelecimento nesta fixture, sem cadastro externo. Componente da chave primária composta.|pk|
|estabelecimento|Nome comercial simulado do estabelecimento.|atributo|

PK no Unity Catalog é informativa: não garante unicidade de futuras escritas. O notebook verifica nulidade e unicidade de todas as versões antes de SET NOT NULL/ADD CONSTRAINT. NOT NULL é validado pelo Delta. Não aplica RELY, não adiciona FK e não altera valores, nomes ou tipos. Campos de PK recebem tag nr_papel=pk; tags são metadados reais, não TBLPROPERTIES. Dados sintéticos não significam que essas tags sejam política de acesso/mascaramento.

Exige SELECT e autorização para alterar tabelas e aplicar tags; tags governadas, se houver colisão com as chaves nr_*, podem exigir ASSIGN. Não contorna erros de permissão. Não sobrescreve tags nr_* existentes com valores divergentes; não remove tags de terceiros. PK preexistente incompatível bloqueia. Operações não são atômicas entre tabelas: falha parcial deve ser retomada com o mesmo notebook, preservando o output. Após aplicação, constraints/colunas/tags são relidas do information_schema. Exportar evidência.

NOT NULL e constraints alteram metadados estruturais Gold, portanto não reexecutar escritores 06/07 para esta tarefa. Depois, repetir 09 com os mesmos snapshots para conferir registros preservados. As descrições são versionadas; comentários anteriores dessas colunas serão atualizados com o dicionário.

Referências: https://docs.databricks.com/aws/en/tables/constraints ; https://docs.databricks.com/aws/en/database-objects/tags ; https://docs.databricks.com/aws/en/comments/
