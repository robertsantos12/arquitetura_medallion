-- Pergunta: como muda o gasto mensal e como se compara aos pares atuais?
-- Grão cliente/mês. Gasto líquido, recusas preservadas no agregado.
-- Esperado qualitativo: variações e quartis, sem afirmar causalidade.
-- Limite: meses sem tentativas não são densificados; LAG compara meses observados.
WITH mensal AS (
 SELECT m.*,d.cidade,d.segmento,
 ROW_NUMBER() OVER(PARTITION BY m.id_cliente,m.mes ORDER BY d.vigente_desde DESC) rn
 FROM h_gold_cliente_mes m JOIN h_gold_dim_cliente d
 ON m.id_cliente=d.id_cliente AND d.vigente_desde < add_months(m.mes,1)
 AND (d.vigente_ate IS NULL OR d.vigente_ate>=add_months(m.mes,1))
), historico AS (
 SELECT *, LAG(valor_liquido) OVER(PARTITION BY id_cliente ORDER BY mes) anterior,
 FIRST_VALUE(valor_liquido) OVER(PARTITION BY id_cliente ORDER BY mes) primeiro,
 AVG(valor_liquido) OVER(PARTITION BY id_cliente ORDER BY mes ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) media_historica,
 AVG(valor_liquido) OVER(PARTITION BY cidade,segmento,mes) media_pares,
 NTILE(4) OVER(PARTITION BY mes ORDER BY valor_liquido,id_cliente) quartil
 FROM mensal WHERE rn=1
)
SELECT *,valor_liquido-anterior variacao,
 CASE WHEN media_historica>0 AND valor_liquido>3*media_historica THEN true ELSE false END anomalia
FROM historico ORDER BY mes,id_cliente
