# Evidências de validação

## Estado atual — 24/10/2026

| Etapa | Resultado | Evidência |
| --- | --- | --- |
| 00 — Delta | Validada | Export enviado pelo responsável, com outputs e sem saídas de erro |
| 01 — Estrutura | Validada | Export com importação do pacote e confirmação dos cinco schemas |
| 02 — Rastreabilidade | Validada pelo output informado pelo responsável | Duas tentativas SUCESSO e uma FALHOU controlada, com 3 eventos e hashes conferidos em cada |
| 03 — Releitura | Implementada; integração pendente | Aguarda os três run_ids produzidos pelo 02 |

Os códigos das células dos exports 00 e 01 correspondem ao commit feab6257ee1389403335eff4be0f72898ca89093. A validação identificou os marcadores de conclusão e os outputs esperados. O contador execution_count=0 do export não foi usado para rejeitar arquivos que possuem resultados.

O teste 00 comprova formato Delta, MERGE, releitura e repetição sem duplicidade para id=1. Não comprova idempotência do futuro pipeline. O 01 comprova os schemas medallion_dev_landing, bronze, prata, ouro e controle no catálogo workspace.

## Arquivamento dos exports

Cópias revisadas de 00 e 01 publicadas com autorização do responsável, sem e-mail ou caminhos pessoais. O código das células foi preservado. [Arquivos e manifesto](evidencias/2026-10-24_exports_revisados/README.md) documentam as remoções e os hashes de entrada e saída. Os módulos importados durante a execução original não tinham snapshot; os exports comprovam o código das células, não a versão exata desses módulos.

A exportação com outputs funcionou. A divergência no caminho de commit pela pasta Git permanece sem causa determinada. Veja docs/rastreabilidade_execucoes.md para a investigação anterior.

## Testes locais da rastreabilidade

Comando: `PYTHONPATH=src python3 -m unittest discover -s tests -v`.

Resultado: 17 testes aprovados. Cobertura: configuração, bootstrap, repetição de lote com tentativas distintas, propagação de erro, falha de persistência, corrupção de arquivos e fontes, eventos duplicados/ausentes, ausência de verificações e execução interrompida.

Esses testes usam arquivos temporários e um destino em memória. Não representam uma execução real em Spark/Delta/Volumes. A sintaxe das células de 02 e 03 foi verificada sem executar Databricks.

## Execução 02 informada pelo responsável

O output enviado confirma RASTREABILIDADE: OK, com três tentativas distintas: SUCESSO, SUCESSO e FALHOU (esperada no teste). Cada tentativa tem 3 eventos e hashes_verificados=True. O hash de código informado coincide com o snapshot local do pacote preparado para essa entrega. O registro estruturado está em [resultado informado](evidencias/2026-10-24_rastreabilidade_02/resultado_informado.json).

A IA não consultou o Delta/Volume diretamente e não recebeu export do notebook 02. A releitura em nova sessão pelo notebook 03 permanece pendente. O resultado informado é preservado como tal, sem fabricar outputs de notebook nem horários ausentes.

## Atualização — Etapa 04 V2 validada em 24/10/2026

O notebook exportado com outputs confirma 21 clientes distintos, 12.158 transações, 138 arquivos novos, três lotes, seis fontes e auditoria final SUCESSO com hashes verificados. RUN_ID: `45599d53-5189-4644-b92a-703eb3b5154d`. O notebook com outputs foi versionado em `notebooks/04_gerar_dados_sinteticos_v2.ipynb` e os detalhes estão em [evidências V2](evidencias/2026-10-24_geracao_sintetica_v2/README.md).

O registro atesta a geração no Databricks, não a ingestão Bronze nem as camadas posteriores. A nota inicial deste documento é um histórico anterior à validação da V2.

## Etapa 05 — Bronze V2 validada (24/10/2026)

Quatro notebooks Databricks com outputs foram recebidos e arquivados na branch `chore/estrutura-inicial`: carga inicial, repetição da inicial, incremental e atrasada. Todos reportam `BRONZE V2: OK` e não têm outputs de erro; contagens finais de transações por lote: 6.080 / 4.560 / 1.518 (12.158). Consulte o [manifesto e os quatro exports](evidencias/2026-10-24_bronze_v2_exports/README.md) para hashes de origem, blobs versionados e limitações da evidência.


## Atualização — preparação para homologação

Preparação 06–09: código/testes locais disponíveis, sem execução Databricks nesta entrega. Coleta obrigatória após cada notebook e novo 09 em sessão limpa; guardar snapshot IDs, run_ids, parâmetros, SHA do commit e exports com outputs. Não editar evidências antigas. Ver homologacao_domingo.md.
