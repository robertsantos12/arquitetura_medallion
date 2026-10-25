-- Pergunta: café de Florinda e rosas de Girafales ocorrem no mesmo dia?
-- Grão dia UTC. Filtra compras aprovadas dos estabelecimentos temáticos.
-- Esperado qualitativo: coincidência em dias alternados, deliberadamente plantada.
-- Limite: coincidência artificial não prova relacionamento causal nem prevê compras.
WITH cafe AS (
 SELECT DISTINCT date(data_transacao) dia FROM h_gold_fato_transacao
 WHERE nome='Dona Florinda' AND estabelecimento='Café e Biscoitos da Vila' AND status_transacao='APROVADA'
), rosas AS (
 SELECT DISTINCT date(data_transacao) dia FROM h_gold_fato_transacao
 WHERE nome='Professor Girafales' AND estabelecimento='Floricultura das Rosas' AND status_transacao='APROVADA'
)
SELECT c.dia,CASE WHEN r.dia IS NULL THEN false ELSE true END rosas_no_mesmo_dia
FROM cafe c LEFT JOIN rosas r ON c.dia=r.dia ORDER BY c.dia
