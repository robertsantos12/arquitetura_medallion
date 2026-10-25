-- Pergunta: quais motivos e valores tentados de Madruga e Chaves?
-- Grão cliente/motivo/status. Recusa não é gasto nem erro de qualidade.
-- Limite: motivos são textos da fixture; não inferir saldo real ou recuperação.
SELECT nome,status_transacao,motivo_recusa,count(*) tentativas,
 sum(valor) valor_tentado,sum(valor_liquido) gasto_efetivo
FROM h_gold_fato_transacao WHERE nome IN ('Seu Madruga','Chaves')
GROUP BY nome,status_transacao,motivo_recusa ORDER BY nome,tentativas DESC
