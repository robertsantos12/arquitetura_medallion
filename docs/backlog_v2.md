# Bloqueios e limitações — homologação e evolução

## Obrigatório na homologação

- PENDENTE: executar notebooks 06–09 no Databricks e coletar exports com outputs. Ambiente local não tem PySpark: MERGE Delta, permissões, SQL e EXPLAIN não foram executados localmente. Não declarar integração aprovada antes da coleta.
- PENDENTE: revisar plano EXPLAIN real e métricas do workspace; ajustes de estratégia só após evidência.
- PENDENTE: formato final do PDF é repositório privado ou pacote compactado. O repositório atual é público por escolha já autorizada; preparar pacote privado na entrega, sem alterar visibilidade automaticamente.
- Reexecução com código alterado gera novo snapshot; usar os IDs correspondentes da mesma versão do código nos notebooks seguintes. Um escritor por vez.

## Decisões aceitas para o case

- Leitura/transformação em Python no driver para ~12 mil transações, limite 100 mil linhas/fonte na leitura Bronze. Snapshot completo a cada nova entrada: reprocessamento correto de atrasos, custo não otimizado. Migrar para DataFrames distribuídos e atualização de chaves/períodos afetados depois.
- Silver/Gold usam MERGE de inclusão por snapshot_id+row_key; não atualizam nem apagam snapshots anteriores. A marca completa fecha a execução lógica, não é transação multi-tabela. Falhas deixam snapshot incompleto retomável; leitores exigem marcador e conferem hashes. Retenção/limpeza e reconciliador automático ficam para evolução.
- CDC D exige payload completo pelo contrato desta versão. Tombstones esparsos precisam contrato próprio. Eventos e histórico são preservados; versões inválidas segregadas não estabelecem vigência.
- Features respeitam corte de tempo de evento, não tempo de disponibilidade. Não alegar ausência de leakage point-in-time por chegada. Treino retrospectivo com dimensões corrigidas exige bitemporalidade.
- Oráculos globais V2 não são fixados artificialmente; verificam-se invariantes e subconjunto V1 R$ 2.270. Há oito inválidos esperados na massa atual; validar no workspace.

## Melhorias da Bronze sem migração arriscada

- Implementado validador somente leitura com unicidade de id_registro, comparação completa com manifesto/controle, payload e SHA. Lidas/existentes e inseridas=0 são métricas do validador, não métricas novas do ingestor.
- Ingestor 05 original ainda verifica hash no controle e não compara payload de todos os matches antes de MERGE. Endurecer o caminho de escrita e métricas de linhas efetivamente inseridas em etapa posterior testada; homologação 06/09 rejeita conflitos já existentes antes de derivar dados.
- arquivo equivale ao arquivo_origem relativo; ingerido_em é timestamp_ingestao (UTC); data_ingestao pode ser derivada. run_id identifica tentativa, não é batch_id. id_registro é hash de posição, não hash_linha do conteúdo. payload_json preserva schema evoluído, mas schema_version não existe fisicamente. Enriquecimento por views/join de auditoria requer teste de vínculo run_id → batch_id. Não afirmar atendimento físico integral dos metadados do PDF; migração compatível adiada para preservar baseline.
- Auto Loader/checkpoints/schema rescue, controle concorrente distribuído, recuperação transacional e CI com Spark/Delta ficam para evolução.

## Nova fixture, sem alterar V2 validada

- Aluguel recebido de Seu Barriga é compra aprovada na origem, não crédito. Criar natureza_movimento e transferência vinculada em V3. Até lá, gasto segue status APROVADA e não demonstra recuperação de aluguel recusado.
- Chaves DEBITO com recusa LIMITE_INSUFICIENTE: corrigir produto/motivo em V3, preservando texto atual.
- V2 cobre 120 dias, 18 nomes temáticos e três IDs V1; não seis meses nem todos os personagens. Expandir somente em nova versão.
- Mais padrões de consumo distintos por personagem, anomalias plantadas, reenvios conflitantes, D esparso e moedas múltiplas ficam para nova fixture.
- Meses sem tentativas não são densificados no SQL: LAG compara meses observados. Pares de cidade/segmento incluem o próprio cliente. Há só 20 clientes válidos; quartis não representam população real.
