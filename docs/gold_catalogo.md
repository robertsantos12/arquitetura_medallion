# Catálogo de negócio Gold

As oito tabelas são físicas Delta; row_key é a chave de MERGE dentro de cada snapshot. O notebook 10 aplica e verifica COMMENT ON TABLE no Unity Catalog, sem alterar linhas. Aplicação ainda pendente no workspace.

|Tabela|Finalidade|Grão|
|---|---|---|
|gold_fato_transacao|Tentativas de pagamento com vínculo temporal válido e valores bruto, estornado e líquido. Recusas/cancelamentos têm gasto zero.|snapshot_id + id_transacao|
|gold_cliente_mes|Comportamento mensal do cliente: tentativas, aprovações, recusas, cancelamentos e valores. Estornos até o corte são atribuídos ao mês da compra.|snapshot_id + id_cliente + mes|
|gold_indicadores_risco|Contagem de eventos e chargebacks por transação, com estornos até o corte. Chargeback não gera segundo débito financeiro.|snapshot_id + id_transacao|
|gold_features_cliente|Frequência, recusa, gasto líquido e recência dos clientes com tentativas até data_corte. Corte por evento, sem garantia de disponibilidade histórica por chegada.|snapshot_id + id_cliente + data_corte|
|gold_dim_cliente|Histórico cadastral do cliente com intervalos [vigente_desde, vigente_ate). Associar fato por cliente_versao = row_key e snapshot_id.|snapshot_id + id_cliente + vigente_desde|
|gold_dim_conta|Histórico da conta e seu estado. Associar fato por conta_versao = row_key e snapshot_id.|snapshot_id + id_conta + vigente_desde|
|gold_dim_cartao|Histórico do cartão, limite e status. Associar fato por cartao_versao = row_key e snapshot_id.|snapshot_id + id_cartao + vigente_desde|
|gold_dim_estabelecimento|Estabelecimentos identificados por hash do nome na fixture. Colisões de nomes comerciais distintos exigirão chave externa futura.|snapshot_id + id_estabelecimento|

Fato usa a dimensão vigente no instante da transação. Dimensões têm múltiplas versões por ID: joins apenas por ID multiplicam valores. Snapshot Gold é próprio: usar as versões copiadas para suas dimensões Gold. valor é tentativa, valor_bruto é apenas aprovada, valor_estornado é abatimento até corte e valor_liquido = bruto - estornado. Indicadores de risco incluem também transações sem risco, com zero eventos. Features não incluem clientes sem tentativas.
