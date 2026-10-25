# Matriz de aderência ao PDF oficial

Revisão de todas as cinco páginas do Desafio Engenharia de Dados Sênior, em 25/10/2026. Esta matriz descreve a entrega observada, não certificação de atendimento integral. V2 abaixo significa evolução da solução; não confundir com a massa sintética V2 já validada.

Legenda: VALIDADO = outputs reais fornecidos pelo operador; TESTADO = teste local; DOCUMENTADO = desenho/justificativa; PARCIAL = lacuna aberta; PENDENTE = ação ainda não concluída. Requisitos obrigatórios parciais não se tornam opcionais por constarem no backlog.

|PDF|Requisito|Estado e evidência|Fechamento / evolução|
|---|---|---|---|
|1–2|Databricks obrigatório|VALIDADO: 00–11, exports em docs/evidencias|Ambiente dev sintético, não produção|
|2|Repositório privado ou pacote compactado|PENDENTE: repositório atual público|Preparar pacote revisado antes de enviar; não alterar visibilidade automaticamente|
|2|Código reproduzível, arquitetura, premissas, limites|DOCUMENTADO: README, architecture, decisions, contratos e guias|Revisar links/versão congelada no pacote|
|2|Sem dados reais/segredos|Fixture sintética e exports novos sanitizados|PENDENTE varredura final de todo o pacote, inclusive exports antigos; não alegar que limpeza de um export saneou todo o histórico Git|
|2|Evidências e idempotência|VALIDADO: 00/02/03/05/06/07/09, hashes, repetição e releitura após reinício|Preservar tentativas falhas e exitosas|
|2|Defesa técnica|PENDENTE preparação do candidato|Defender desenho e limitações, inclusive uso de IA|
|3|Seis fontes com campos mínimos|VALIDADO: fixture V2, contratos, Bronze|CPF é token fictício; valor_estorno e status são extensões documentadas|
|3|Qualidade, atualizações, atraso e eventos de negócio|TESTADO/VALIDADO: duplicatas, vínculos inválidos, versões intermediárias, estornos|Padrões narrativos mais variados em nova fixture, sem alterar bytes atuais|
|5 Bronze|Ingestão incremental, Delta|VALIDADO: quatro exports 05, lote inicial/repetido/incremental/atrasado|Driver para fixture pequena; Auto Loader distribuído em evolução|
|5 Bronze|Preservar bruto e schema inesperado|VALIDADO: payload_json, dispositivo e cabeçalhos evoluídos|Normalização semântica de opcionais vazios na Silver|
|5 Bronze|arquivo_origem e timestamps|PARCIAL NOMINAL: arquivo relativo e ingerido_em existem; data_ingestao derivável|Documentar equivalência e expor contrato nominal via migração/view testada|
|5 Bronze|batch_id, hash_linha, schema_version|PARCIAL OBRIGATÓRIO: run_id não é batch_id; id_registro é hash de posição, não de conteúdo; sem coluna física schema_version|Recomendado resolver antes de main com enriquecimento compatível e testes, sem recriar Bronze. Enquanto aberto, declarar aderência parcial e risco de avaliação|
|5 Bronze|Justificativa Auto Loader|DOCUMENTADO: docs/bronze_v2.md e particionamento_e_streaming.md|PDF permite justificar alternativa; não exige stream em produção no case|
|5 Prata|Seis tabelas tipadas e quarentena|VALIDADO: 06/09, 12.153 transações válidas e oito registros em quarentena|Quarentena com fonte/payload/motivo; linhagem de posição completa permanece Bronze|
|5 Prata|SCD2 clientes/contas/cartões|TESTADO/VALIDADO: intervalos, tombstone completo, recomposição CDC atrasado|CDC esparso/bitemporalidade em evolução|
|5 Prata|MERGE incremental e idempotência|VALIDADO: inclusão por snapshot+row_key, repetição sem inserção|Recomposição completa por cenário é trade-off declarado; incremental por chaves afetadas em evolução|
|5 Prata|Atrasos/reprocessamento por data|TESTADO/VALIDADO: data base e snapshots recompostos sem apagar anteriores|Não é reprocessamento seletivo de uma partição de evento|
|5 Prata|Financeiro, cancelamentos/recusas/estornos|VALIDADO: 08/09; recusas com gasto zero; V1=2270,00|Chargeback é risco, sem segundo débito; narrativa aluguel recebimento permanece limitada|
|5 Ouro|Fato com grão, quatro dimensões|VALIDADO: 07, 10 e 11; grãos, descrições, PK e tags|PK informativa; testes continuam responsáveis pela unicidade|
|5 Ouro|Cliente/mês, indicadores risco, features|VALIDADO: 94 agregados, 12.153 indicadores e 20 features|Corte por evento, não disponibilidade histórica; não alegar point-in-time por chegada|
|5 Ouro|Chaves, filtros, granularidade e regras|DOCUMENTADO/VALIDADO: catálogo, 98 descrições, PKs e tags|Filtrar snapshot completo; não somar snapshots|
|6 SQL|CTEs, ROW_NUMBER, LAG, FIRST_VALUE, NTILE|VALIDADO: 08, sql/01_comportamento.sql|Janelas com meses observados, sem densificar meses vazios|
|6 SQL|Anomalias e comparação com histórico/cidade/segmento|VALIDADO execução: regra de três vezes média histórica e pares por grupo|Não exige anomalia positiva na fixture; pares incluem o próprio cliente e amostra é pequena|
|6 SQL|MERGE SQL/PySpark|VALIDADO: Bronze/snapshots|Não confundir com atomicidade multi-tabela|
|7|Módulos, separação, notebooks finos|IMPLEMENTADO: src/medallion, tests, sql, notebooks|11/12 complementam governança, não substituem camadas|
|7|Logs, exceções e parametrização|VALIDADO/DOCUMENTADO: AuditRun 06/07, controles, erros propagados|Dev limitado por segurança; Gold não tem implantação prod; enriquecer observabilidade de todas as etapas em evolução|
|7|Testes unitários e transformação|TESTADO: 40 testes locais no fechamento, incluindo regras e dublês de persistência/API|Dublês não são integração Databricks; outputs reais separados|
|8|Particionamento/clustering/OPTIMIZE|DOCUMENTADO: sem partições no volume pequeno, critérios em particionamento_e_streaming.md|Não exige aplicar otimização desnecessária; medir bytes/arquivos antes de mudar layout|
|8|Arquivos pequenos/crescimento|DOCUMENTADO: evitar alta cardinalidade, compactação por métricas|Benchmark e automação em evolução|
|8|Monitorar falhas/volume/qualidade|IMPLEMENTADO/DOCUMENTADO: auditoria, recontagens, quarentena|Dashboard, alertas/SLAs automatizados em evolução|
|8|Unity Catalog: catálogos/schemas/permissões|DOCUMENTADO/VALIDADO: schemas dev, comentários/PK/tags|Privilégio de external metadata ausente; não é prova de limitação comercial Free|
|8|Agendamento Workflows|DOCUMENTADO: ordem tarefas, concorrência 1 e retries|Job não criado; exigência é documentar como seria agendado|
|8|Plano ou estratégia de joins|VALIDADO export EXPLAIN 08 + comentário técnico|Há plano Photon/adaptativo e exchanges; perfil/benchmark completo não medido|
|9|Múltiplas contas/cartões por cliente|TESTADO: C001 com A001/A002, K001/K002|Casos V1 incorporados à V2|
|9|Mudança status, cancelamento futuro e histórico|TESTADO/VALIDADO: K002 e T005 segregada, transação anterior preservada|Teste temporal não depende de nome do personagem|
|9|Estorno sem gasto indevido e versão vigente|TESTADO/VALIDADO: oráculo e chaves de versão na fato|Estorno parcial abate; total zera|
|9|Arquivos fora de ordem e mesmo ID em cargas|VALIDADO 05/06/09: terceiro lote atrasado e T001 repetida|Atualizações conflitantes segregadas|
|Git|Branches, commits, README, ignore e dependências|IMPLEMENTADO: chore/estrutura-inicial, develop e main|Nenhum merge efetuado pelo assistente nesta revisão; PR ainda por abrir|
|Git diferencial|CI simples|NÃO IMPLEMENTADO, diferencial opcional|V2: GitHub Actions unitários/lint e integração Spark controlada|
|10|Pacote/documentos/notebooks/SQL/testes/evidências/trade-offs|IMPLEMENTADO conteúdo; pacote final PENDENTE|Usar roteiro_entrega.md e congelar SHA|
|Extra usuário|Linhagem visual Gold→Silver→Bronze|BLOQUEADA: 12 PermissionDenied CREATE EXTERNAL METADATA|Não é requisito explícito do PDF. Mapa/código disponíveis; liberar privilégio ou captura nativa Spark/SQL em evolução|

## Conclusão da revisão

O fluxo de dados e os complementos de governança 10/11 têm outputs reais. Não declarar 100% de aderência: metadados obrigatórios Bronze permanecem parciais; formato privado/compactado, revisão de informações sensíveis e preparação de defesa ainda precisam fechamento. A linhagem visual é melhoria adicional bloqueada, não deve ser usada para desqualificar a validação financeira nem apresentada como concluída.
