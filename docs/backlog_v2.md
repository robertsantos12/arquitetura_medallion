# Bloqueios e limitações — homologação e evolução

## Obrigatório na homologação

- CONCLUÍDO por outputs do operador: 06–09, inclusive releitura após reinício e 09 após metadados; 10/11 também concluídos. 12 bloqueado conforme registro abaixo.
- PENDENTE: revisar plano EXPLAIN real e métricas do workspace; ajustes de estratégia só após evidência.
- PENDENTE: formato final do PDF é repositório privado ou pacote compactado. O repositório atual é público por escolha já autorizada; preparar pacote privado na entrega, sem alterar visibilidade automaticamente.
- Reexecução com código alterado gera novo snapshot; usar os IDs correspondentes da mesma versão do código nos notebooks seguintes. Um escritor por vez.

## Decisões aceitas para o case

- Leitura/transformação em Python no driver para ~12 mil transações, limite 100 mil linhas/fonte na leitura Bronze. Snapshot completo a cada nova entrada: reprocessamento correto de atrasos, custo não otimizado. Migrar para DataFrames distribuídos e atualização de chaves/períodos afetados depois.
- Silver/Gold usam MERGE de inclusão por snapshot_id+row_key; não atualizam nem apagam snapshots anteriores. A marca completa fecha a execução lógica, não é transação multi-tabela. Falhas deixam snapshot incompleto retomável; leitores exigem marcador e conferem hashes. Retenção/limpeza e reconciliador automático ficam para evolução.
- CDC D exige payload completo pelo contrato desta versão. Tombstones esparsos precisam contrato próprio. Eventos e histórico são preservados; versões inválidas segregadas não estabelecem vigência.
- Features respeitam corte de tempo de evento, não tempo de disponibilidade. Não alegar ausência de leakage point-in-time por chegada. Treino retrospectivo com dimensões corrigidas exige bitemporalidade.
- Oráculos globais V2 não são fixados artificialmente; invariantes e subconjunto V1 R$ 2.270 foram confirmados no workspace. Oito registros em quarentena foram confirmados.

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


## Bloqueio confirmado — notebook 12, 25/10/2026

Tentativa real falhou na primeira criação de metadado externo: PermissionDenied, falta CREATE EXTERNAL METADATA no metastore. Não é prova de indisponibilidade da edição Free. Nenhuma aresta confirmada; linhagem visual declarada NÃO VALIDADA. Evidência sanitizada em docs/evidencias/2026-10-25_linhagem_12_bloqueada. Sem alteração de permissões ou dados pelo revisor. Resolução depende de responsável autorizado do metastore ou ambiente que disponibilize o privilégio. Para entrega atual manter mapa/código documentados e a limitação explícita; não bloquear o fechamento financeiro já validado por esse complemento. Captura nativa depende da evolução Spark/SQL, sem reprocessamento artificial de snapshots históricos.


## Priorização revisada contra TODO o PDF — 25/10/2026

Referência completa: matriz_requisitos_pdf.md (seções 1–10 e Git). V2 aqui significa evolução da solução, não a massa V2 congelada.

|Prioridade|Tema|Ação e aceite|
|---|---|---|
|P0 antes de main|Metadados Bronze obrigatórios PARCIAIS|Complemento compatível, testado e homologado de batch_id, hash_linha e schema_version; arquivo/data/timestamp nominais com semântica clara. Sem recriar dados. Enquanto aberto, não declarar cumprimento integral.|
|P0 entrega|Formato privado/ZIP e revisão de informações pessoais|Congelar SHA, varrer conteúdo, preparar cópia revisada e manifesto; não alterar visibilidade nem histórico sem autorização.|
|P0 revisão|PRs, evidências e defesa|Revisar chore→develop, depois develop→main; preparar defesa técnica e registrar aceite/ressalvas.|
|P1 V2 solução|Captura nativa de linhagem e escala|Spark DataFrames/SQL com regressão num destino controlado; manter regras temporais/financeiras. Privilégio de linhagem declarada depende de administrador.|
|P1 V2 solução|Auto Loader/streaming|Envelope versionado, offsets/chaves, checkpoint por fonte, microlotes idempotentes, watermark por SLA, cutover e rollback reconciliados.|
|P1 V2 solução|Fortalecer escrita Bronze|Detectar conflito em matches antes de MERGE, métricas efetivas inseridas/existentes, concorrência e recuperação de falhas. Validador readonly atual não substitui isso.|
|P1 V2 solução|Incremental por chaves/períodos|Recompor apenas afetados com testes de equivalência ao snapshot completo.|
|P1 V2 solução|Features point-in-time por chegada|Disponibilidade e bitemporalidade; corte de evento atual não garante ausência de leakage por chegada.|
|P2 V2 solução|Observabilidade/operacionalização|Workflows efetivo, alertas, SLAs, dashboards DQ/volumetria, reconciliação e retenção sem apagar evidências. Documento de agendamento atual atende a explicação, não implantação.|
|P2 V2 solução|Layout/performance|Medir sizeInBytes/numFiles, planos/perfil, spill/bytes/duração; avaliar Liquid Clustering e OPTIMIZE por necessidade, sem particionar a fixture pequena.|
|P2 V2 solução|CI/integracão Spark|CI unitários/lint (diferencial do PDF) e integração controlada Spark/Delta/API.|
|P2 fixture futura|Narrativa e amostragem|Natureza financeira e vínculo para aluguel, produto/motivo coerentes, mais meses/personagens/padrões/anomalias, moedas e tombstones esparsos. Nova versão, não modificar massa V2.|
|P2 análise|Calendário/pares|Densificar meses vazios, pares sem incluir o próprio cliente, ampliar amostra e critérios de anomalia.|

O backlog não dispensa requisitos obrigatórios. Metadados Bronze P0 são lacuna da entrega inicial, não opcional. A linhagem visual adicional é bloqueio distinto; nenhum teste/merge deve apresentá-la como aprovada. Fontes, planos e toda evidência anterior permanecem preservados.
