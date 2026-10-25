# Contratos de origem — cenário sintético v1

O PDF define os campos mínimos; esta versão acrescenta `valor_estorno` para suportar estorno parcial e `status_transacao` para cancelamento. A Bronze preservará o conteúdo bruto e campos novos. Este documento define as regras planejadas para a Prata; essa camada ainda será implementada. Datas de evento são ISO 8601 UTC; datas sem horário usam YYYY-MM-DD. Valores monetários são strings decimais na origem e serão DECIMAL(18,2) na Prata. IDs são STRING, sem conversão para inteiro.

| Fonte/formato | Campos mínimos | Chave e regra planejada |
|---|---|---|
| clientes_cdc/JSON Lines | id_cliente, cpf, nome, cidade, estado, renda, segmento, data_atualizacao, operacao | Histórico por id_cliente + data_atualizacao; renda não negativa; estado válido |
| contas_cdc/JSON Lines | id_conta, id_cliente, tipo_conta, status_conta, data_abertura, data_atualizacao, operacao | Histórico por id_conta + data_atualizacao; cliente deve existir temporalmente |
| cartoes_cdc/JSON Lines | id_cartao, id_conta, tipo_cartao, limite, status_cartao, data_atualizacao, operacao | Histórico por id_cartao + data_atualizacao; limite não negativo e conta válida |
| transacoes/CSV UTF-8 | id_transacao, id_cartao, data_transacao, valor, mcc, estabelecimento, canal, pais, moeda; adicional status_transacao | Grão id_transacao; valor positivo, BRL, cartão/conta válidos e ativos na data; cancelada fora das métricas |
| eventos_risco/CSV UTF-8 | id_evento, id_transacao, tipo_evento, severidade, data_evento | Grão id_evento; vínculo com transação; tipos SUSPEITA/FRAUDE/CHARGEBACK |
| estornos/CSV UTF-8 | id_estorno, id_transacao, data_estorno, motivo; adicional valor_estorno | Grão id_estorno; valor positivo, vínculo válido e total acumulado até o valor original |

CSV tem cabeçalho e separador vírgula. CDC usa I/U/D como domínio reservado, mas esta fixture exercita I/U e encerramento/cancelamento por status; exclusão física não é simulada. Duplicatas exatas são deduplicadas. Conflitos com mesma chave e timestamp serão segregados; não escolher silenciosamente uma versão. SCD2 usa intervalos [vigente_desde, vigente_ate), incluindo reconstrução para versões atrasadas.

`cpf` contém tokens `CPF_SINTETICO_<id>`, deliberadamente sem documentos reais. Nesta fixture o contrato aceita esse domínio sintético; validar CPF real/checksum fica fora do teste. Nomes, estabelecimentos e dispositivos também são artificiais. Não há dados reais.

## Estrutura e ordem de chegada

`/Volumes/<catalogo>/medallion_dev_landing/arquivos/cenarios/v1/<data_referencia>/<lote>/<fonte>/...`

Cada lote é uma chegada lógica independente. A data do diretório de transações é data de negócio, não de ingestão. O manifesto identifica caminhos, contagens, hashes, versão e ordem de chegada. Lotes sem registros de uma fonte não têm arquivo vazio dessa fonte.

| Chegada | Cenários |
|---|---|
| 01_inicial | C001 tem A001/A002 e K001/K002; duplicata de cliente e T001; renda inválida; conta sem cliente; cartão sem conta; transação negativa, cartão inexistente e transação cancelada; estorno parcial de T002 |
| 02_incremental | C001 muda cidade/renda; A002 encerra; K001 muda limite; K002 cancela; T001 reaparece; campo dispositivo; T005 após cancelamento; mês seguinte; chargeback e vínculo de risco inválido; estorno total de T003 e referência inválida |
| 03_atrasado | Versão C001 com timestamp intermediário; T007 anterior à segunda chegada e T008 do mês anterior |

Com data base 2026-01-15, C001 tem versão inicial de 06/12/2025, depois uma versão 17/01/2026 e, no terceiro lote, uma versão 16/01/2026. A versão 16/01 precisa ocupar o intervalo até 17/01 sem apagar a versão mais recente. Os cadastros iniciais antecedem também T008, de 15/12/2025.

## Oráculo financeiro planejado para os testes da Prata/Ouro

Considerando todos os lotes, deduplicação por ID, vínculos temporais válidos, exclusão de canceladas/inválidas e estorno parcial abatido do valor bruto:

| Transação | Valor bruto | Líquido esperado | Motivo |
|---|---:|---:|---|
| T001 | 100,00 | 100,00 | Três cópias, uma transação |
| T002 | 200,00 | 150,00 | Estorno parcial 50,00; transação anterior ao encerramento preservada |
| T003 | 300,00 | 0,00 | Estorno total 300,00; chargeback é sinal de risco, sem segundo débito financeiro |
| T004 | 400,00 | 400,00 | Válida, schema evoluído |
| T006 | 1.500,00 | 1.500,00 | Mês seguinte, válida |
| T007 | 70,00 | 70,00 | Atrasada, válida |
| T008 | 50,00 | 50,00 | Mês anterior, válida |

Total líquido esperado: **2.270,00**. T_NEG, T_BAD_CARD e T005 devem ir para quarentena pelas regras de validade; T_CANCEL deve ser preservada com status, excluída das métricas. O total é um oráculo planejado, ainda não resultado de transformação executada. Eventos/estornos inválidos não alteram os valores. Histórico temporal e estorno parcial precisam ser defendidos explicitamente no produto final.


## Atualização — preparação para homologação

Adendo vigente para Silver/Gold: contrato_homologacao.md define APROVADA/RECUSADA/CANCELADA, normalização de campos opcionais vazios do CSV, SCD2, D com payload completo, decimal, BRL e estornos. Oráculo 2270 refere-se somente ao subconjunto V1 incorporado. Não alterar a massa V2.
