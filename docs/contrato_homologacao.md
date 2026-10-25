# Contrato de homologação Silver/Gold

Baseline congelada: massa V2, 21 IDs de cliente de origem (inclui cadastro inválido), 12.158 linhas de transação Bronze, três lotes. Não regenerar 04 nem reingerir 05 para homologar 06–09.

APROVADA gera gasto se o vínculo temporal estiver válido. RECUSADA e CANCELADA são tentativas válidas com gasto zero; não vão à quarentena pelo status. Valores inválidos, status desconhecido e vínculos inexistentes/inativos vão à quarentena com payload e motivo. Campos extras permanecem no payload_json. Moeda aceita: BRL. CPF é token sintético, sem validação de CPF real.

Estorno parcial abate valor aprovado; total zera o líquido. Estornos anteriores à compra, de tentativas não aprovadas, negativos, com referência inexistente ou cujo acumulado excede a compra são segregados (todos os estornos do grupo excessivo). Chargeback é indicador de risco, sem segundo débito. Eventos futuros ao corte não entram no financeiro/features. Data de corte é inclusiva até 23:59:59.999999 UTC; não representa disponibilidade histórica do dado: features são retrospectivas por tempo de evento, não treinamento point-in-time por chegada.

CDC I/U/D: SCD2 por ID, ordenado por timestamp, intervalos [início,fim). D é tombstone. Duplicata idêntica colapsa; conflitos com mesma chave/timestamp segregam todas as variantes, sem desempate arbitrário. Versões atrasadas recompõem intervalos no novo snapshot. Conta deve ter cliente na atualização, cartão deve ter conta/cliente na atualização e transação precisa dos três vínculos vigentes no evento. Cadastro antigo permanece histórico após encerramento/cancelamento.

Grãos físicos incluem snapshot_id e row_key. Snapshot_id incorpora entrada, corte e código. MERGE insert-only rejeita divergência de conteúdo em chave existente. Nenhum DELETE, UPDATE ou overwrite. Snapshot só pode ser consumido após marcador completo. Reprocessamento lê toda a Bronze da data_referencia e reconstrói todos os períodos; adequado aos 12 mil registros do desafio, não é incremental por partição em escala. Nova chegada gera novo snapshot, repetição idêntica não duplica. Um escritor por vez.

Inconsistência narrativa: V2_ALUGUEL_PAGO_* é compra APROVADA de Seu Barriga, sem natureza de crédito ou vínculo a V2_ALUGUEL_REC_*. Mantemos como gasto conforme contrato de origem; não inferimos recebimento, saldo, recuperação ou transferência. Chaves tem cartão DEBITO na fixture, mas recusa LIMITE_INSUFICIENTE; motivo é texto de origem, não inferência de produto. V2 tem 120 dias e 18 nomes temáticos, além dos 3 IDs V1, não seis meses nem elenco exaustivo. Corrigir apenas em fixture futura versionada.

Oráculo V1: T001=100; T002=150; T003=0; T004=400; T006=1500; T007=70; T008=50; soma 2270. Não é total da V2. Esperar T_NEG/T_BAD_CARD/T005 em quarentena e T_CANCEL com gasto zero. Para a V2 usar contagens observadas e invariantes, sem total financeiro inventado.
