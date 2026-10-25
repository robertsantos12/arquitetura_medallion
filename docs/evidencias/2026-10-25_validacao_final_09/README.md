# Validação final 09 — export revisado

O export contém VALIDAÇÃO FINAL: OK, com data_referencia=2026-01-15, corte=2026-05-31 e os mesmos snapshots da coleta 06/07. Bronze: 12.158 transações de origem; Silver: 12.153 transações e oito registros na quarentena; Gold: 12.153 fatos, 94 cliente/mês e 20 features. Oráculo do subconjunto V1: R$ 2.270,00. Nenhum output de erro encontrado.

A leitura não inseriu linhas Bronze (inseridas=0). Conforme o código do validador, a conclusão exige reconciliação manifesto/Bronze, comparação Silver e Gold recalculadas, unicidade, intervalos SCD2, financeiro e oráculo V1. Resultados são os emitidos no Databricks e enviados pelo operador; não houve consulta direta pelo revisor.

A execução em sessão Python limpa ainda não foi confirmada. Notebook 10 de comentários Gold continua pendente de coleta. Não declarar homologação completa dessas duas condições. O export anterior sem output final não foi usado como prova de sucesso.

Cópia pública com metadados pessoais removidos; hashes e parâmetros no manifesto. Para importar, remova somente .json de .ipynb.json. Evidências anteriores preservadas.
