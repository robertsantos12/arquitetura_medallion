-- Pergunta: risco, chargebacks e estornos por cliente, até o corte?
-- Grão cliente. Eventos contam separados, sem multiplicar valor por join 1:N.
-- Limite: chargeback não é abatido de novo do líquido.
SELECT r.id_cliente,sum(r.eventos) eventos,sum(r.chargebacks) chargebacks,
 sum(r.valor_estornado) estornos,sum(f.valor_liquido) valor_liquido
FROM h_gold_indicadores_risco r JOIN h_gold_fato_transacao f USING(id_transacao)
GROUP BY r.id_cliente ORDER BY eventos DESC
