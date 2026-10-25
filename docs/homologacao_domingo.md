# Homologação de domingo — começar às 11h

## Estado real

IMPLEMENTADO: contratos, validador Bronze somente leitura, Silver tipada das seis fontes, quarentena, SCD2 com atraso, vínculo temporal, Gold, SQL avançado, snapshots imutáveis e validação final.
TESTADO LOCALMENTE: regras puras sobre V1 e CSV/JSON V2 serializados, determinismo sob ordem invertida, financeiro e corte temporal. Consulte tests/test_homologacao.py.
VALIDADO NO DATABRICKS ANTES DESTA ENTREGA: 00–05 conforme exports/histórico. Nenhum output novo foi criado.
PENDENTE: 06–09 no Databricks; MERGE, SQL e plano real. Limitações: backlog_v2.md.

## Sequência, um notebook por vez

1. Faça Pull de chore/estrutura-inicial. Preserve os exports antigos. Não execute 04 ou 05 novamente. Use nova sessão Python após o Pull para evitar imports antigos.
2. Abra 06_processar_silver. Execute só CMD 1. catalogo=workspace, data_referencia=2026-01-15. Depois CMD 2 e CMD 3. Esperado qualitativo: SILVER HOMOLOGAÇÃO: OK e auditoria SUCESSO. Registre SNAPSHOT_SILVER. O módulo executa o MERGE duas vezes e exige zero inserções na repetição. Exporte com outputs e revise antes do próximo notebook.
3. Abra 07_construir_gold. CMD 1: mesmos catálogo/data, snapshot_silver=SHA256 do 06, data_corte=2026-05-31. Depois CMDs 2–3. Registre SNAPSHOT_GOLD. Esperado GOLD HOMOLOGAÇÃO: OK; reconciliação mensal e repetição aprovadas. Exporte e revise.
4. Abra 08_analises_sql. CMD 1: catálogo/data e snapshot_gold=SHA256 do 07. Execute os demais. Arquive os quatro resultados e EXPLAIN FORMATTED. Verifique recusa sem gasto, café/rosas coincidentes e variação mensal. Coincidência não é causalidade. Exporte e revise.
5. Abra 09_validar_pipeline. CMD 1: catálogo/data, snapshot_silver e snapshot_gold correspondentes, data_corte=2026-05-31. Execute os demais. Esperado VALIDAÇÃO FINAL: OK; comparação integral Bronze→Silver→Gold, unicidade, intervalos, recusas/estornos e oráculo V1=2270.00. Exporte e revise.
6. Para comprovar independência da memória, reinicie o Python e repita apenas 09 com os mesmos IDs. Para comprovar repetição de execução, rode 06/07 com o mesmo código/entrada e confirme mesmo snapshot_id, zero novas linhas e mesmos hashes. Cada tentativa auditada tem run_id próprio.

Não cole snapshot_id de Gold no campo Silver. Não troque data_corte entre 07 e 09. IDs são SHA256, não UUIDs de auditoria. Se houver falha, preserve a saída e pare; não faça DROP, DELETE ou overwrite. A retomada com mesmos parâmetros completa apenas linhas faltantes e rejeita divergências.

## Tabelas e grãos

Silver no schema medallion_dev_prata: silver_clientes_cdc/contas_cdc/cartoes_cdc (ID+vigente_desde), silver_transacoes (id_transacao), silver_eventos_risco (id_evento), silver_estornos (id_estorno), silver_quarentena (hash de fonte/payload/motivo). Todas incluem snapshot_id e row_key. DECIMAL(18,2), timestamps UTC e DATE explícitos.

Gold no schema medallion_dev_ouro: gold_fato_transacao (id_transacao; inclui tentativas recusadas/canceladas com gasto zero), gold_cliente_mes (cliente+mês de transação), gold_indicadores_risco (transação, contagens de eventos/chargeback e estornos até corte), gold_features_cliente (cliente+corte, frequência/recusa/gasto/recência) e gold_dim_cliente/conta/cartao (históricas), gold_dim_estabelecimento (hash do nome). Fato armazena as chaves das três versões vigentes; não usar join só por ID contra dimensão histórica.

Filtro obrigatório: snapshot_id. Não somar vários snapshots. Gold mensal reflete estornos conhecidos até o corte na competência da compra original. Taxa de aprovação pode ser derivada de aprovadas/tentativas. Features incluem clientes com tentativas até corte; clientes sem tentativa não têm linha. Quarentena mantém payload_json e motivo; rastreio de posição está na Bronze original, não é replicado integralmente nas tabelas derivadas.

## Operação e defesa

A hipótese de escala é fixture pequena. Sem particionamento físico neste volume para evitar arquivos pequenos. Em produção avaliar Liquid Clustering por chaves de consulta e OPTIMIZE após métricas; não executar otimizações de produção nesta entrega. SQL agrega risco antes/por transação e evita multiplicação financeira em joins 1:N. EXPLAIN deve ser revisado para scans, filtros snapshot_id, exchanges e joins; não há plano observado ainda.

Workflows proposto: tarefas 06→07→08→09, parâmetros de IDs transmitidos entre tarefas, max_concurrent_runs=1, retries limitados e alerta em falha. Ainda não foi criado Job. UTC explícito, permissões USE CATALOG/SCHEMA, SELECT Bronze, CREATE TABLE e MODIFY nos schemas derivados, READ/WRITE no Volume de evidências. Princípio de mínimo privilégio; só dados sintéticos. Git com commits incrementais, sem merge develop/main.

Exporte IPYNB com outputs antes de limpar sessão. Faça commit de validação, mas confira o export: Git dos notebooks pode não conter outputs. Arquive nova coleta com manifesto/hash e revisão de dados pessoais, sem modificar evidências históricas.
