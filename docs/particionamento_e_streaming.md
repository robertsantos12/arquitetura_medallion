# Layout físico e evolução de ingestão

## Decisão para a entrega inicial

Manter tabelas Delta sem particionamento físico: a fato tem 12.153 linhas por snapshot, agregado mensal 94, features 20 e dimensões 11–23. Quantidade de linhas não é tamanho em bytes: medir DESCRIBE DETAIL (sizeInBytes, numFiles, partitionColumns) antes de qualquer mudança. Diretórios data= dos CSVs são organização da landing, não particionamento Delta. Não particionar por cliente, cartão, ID de transação ou snapshot_id: alta cardinalidade criaria partições/arquivos pequenos.

|Grupo|Decisão atual|Evolução condicionada às métricas|
|---|---|---|
|Bronze raw_*|Sem partições; preservar schema e baseline|Auto Loader, compactação e layout por padrão de leitura|
|Fato/risco|Sem partições; filtro snapshot_id obrigatório|Avaliar Liquid Clustering por snapshot_id, data_transacao e/ou id_cliente; poucas chaves escolhidas por workload, não habilitar automaticamente|
|Cliente/mês e features|Sem partições|Clustering por cliente/mês/corte se tamanho e leituras justificarem|
|Dimensões SCD2|Sem partições|Avaliar clustering por ID e início de vigência se crescerem|

Orientação Databricks: não particionar tabelas abaixo de 1 TB; se particionamento estático for escolhido, buscar pelo menos 1 GB por partição. Esses números são critérios de revisão, não promessa de performance. Para tabelas novas, avaliar Liquid Clustering como alternativa ao particionamento/ZORDER; não combinar essas estratégias indiscriminadamente.

Rotina futura: observar bytes lidos, duração p50/p95, frequência de MERGE, tamanho/quantidade de arquivos e crescimento por snapshot. Compactar com OPTIMIZE quando arquivos pequenos elevarem custo de leitura, após baseline e medição antes/depois. Não executar OPTIMIZE/ZORDER/CLUSTER BY nesta entrega sem necessidade demonstrada. Evitar repartition(1) e partições diárias minúsculas. Política de retenção dos snapshots precisa preservar evidências; nenhum VACUUM/DELETE está autorizado por este documento.

O export 08 contém plano Photon/AdaptiveSparkPlan e exchanges de shuffle para consultas com joins/janelas. Plano não equivale a perfil de execução ou benchmark: ainda medir bytes/duração/spill e estratégia final antes de alegar otimização.

Referências: https://docs.databricks.com/aws/en/tables/partitions e https://docs.databricks.com/aws/en/lakehouse-architecture/performance-efficiency/best-practices

## CSV e streaming: separar formato, origem e modo

CSV é formato; streaming é modo de processamento. CSV pode chegar continuamente via Auto Loader. Kafka/Event Hubs pode trazer JSON/Avro; trocar apenas o path não converte o pipeline atual em streaming. O desenho abaixo está MAPEADO, não implementado nem validado.

Contrato de adaptação proposto: fonte, versao_contrato, origem_tipo, formato, identificador_origem, payload_json, timestamp_evento, timestamp_ingestao, schema_version, batch_id, run_id e hash_payload. Adaptador de arquivos identifica path+SHA+linha; adaptador de eventos identifica tópico+partição+offset e, quando disponível, event_id de negócio. Não reinterpretar offsets como número de linha nem reutilizar o atual id_registro para outra semântica.

Configuração futura por fonte: source_type (files/autoloader/kafka), path ou tópico, formato, schema_location, checkpoint_location, trigger e referência de secret. Segredos ficam fora do Git. Consumidores recebem o mesmo envelope Bronze versionado; regras Silver/Gold independem do conector. Separar checkpoint/schema_location por ambiente/fonte/versão. O ingestor atual continua batch de arquivos no driver; não existe chave de configuração que o transforme em stream hoje.

Plano de migração V2:
1. Definir envelope compatível, identidade, semântica de atualização e limites de atraso. Criar adaptador distribuído e testes com eventos duplicados, fora de ordem e schema evoluído.
2. Implantar em destino de homologação separado com checkpoint novo e offsets/cutover documentados. Preservar checkpoint e arquivos antigos. Não reutilizar checkpoint de fonte incompatível.
3. Reproduzir um intervalo conhecido e reconciliar contagens, hashes e valores por chave. Executar em paralelo controlado sem misturar destinos de validação e oficiais.
4. Testar crash após escrita antes do checkpoint: foreachBatch pode repetir microlote; MERGE por chave estável deve ser idempotente. batchId de streaming não substitui batch_id de negócio e reinicia com outro checkpoint.
5. Estabelecer watermark por SLA observado. Atrasos além do limite devem ter trilha de reconciliação/reprocessamento, sem descarte silencioso de finanças. CDC SCD2 e estornos precisam recompor chaves/períodos afetados.
6. Aprovar corte, registrar último offset/arquivo de cada origem e habilitar o novo consumidor. Rollback usa configuração/destino anteriores e reconciliação; nunca apagar estado para simular sucesso.

Começar por Auto Loader para arquivos contínuos é a migração mais próxima do caso atual. Kafka requer conector/autorização específicos. Em produção migrar transformação em memória para DataFrames e snapshots completos para recomposição de chaves/períodos. Não prometer exactly-once entre múltiplas tabelas por existir checkpoint.

Referências: https://docs.databricks.com/aws/en/structured-streaming/checkpoints e https://docs.databricks.com/aws/en/structured-streaming/foreach

## Situação após revisão de 06–08

06/07 apresentam SUCESSO e hashes verificados. Silver: 12.153 transações e 8 registros de quarentena. Gold: fato 12.153, cliente/mês 94 e features 20. 08 executou as quatro consultas (94/4/60/20 linhas); a exibição de algumas consultas mostra só as primeiras 30. Chaves tem 17 recusas e Madruga 4, ambas com gasto zero. Ainda falta 09 com os dois snapshots e corte 2026-05-31, depois repetir 09 em sessão limpa. Aplicar comentários do notebook 10 e coletar seu output. Revisar permissões/README de entrega e preparar pacote privado conforme PDF. Job/streaming/benchmark e melhorias físicas permanecem V2.
