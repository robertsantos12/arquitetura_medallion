# Revalidação das instruções e widgets — 24/10/2026

Quatro exports com outputs enviados pelo usuário e revisados. Código das células comparado ao estado da branch no momento da coleta; sem divergências. Nenhum output de erro encontrado.

| Notebook | Resultado observado |
|---|---|
| 00 | Delta, MERGE, atualização e repetição sem duplicidade: OK |
| 01 | Pacote importado, configuração validada e cinco schemas dev disponíveis |
| 02 | Duas tentativas SUCESSO e uma FALHOU deliberada, três eventos por tentativa, hashes verificados |
| 03 | Releu os mesmos três run_ids do 02, com resultados e hashes coincidentes |

O export 03 comprova o resultado da releitura; não comprova que a sessão Python foi reiniciada. Essa condição depende de confirmação do operador. As verificações de hashes são resultados emitidos pelo código no Databricks; esta revisão não acessou diretamente o Volume/Delta. Os exports não incluem os arquivos JSON completos do Volume. O notebook 01 apresenta um caminho planejado, sem validar o Volume de entrada.

O manifesto contém hashes dos uploads originais e cópias publicadas, além dos run_ids. Metadados Databricks e caminhos pessoais foram removidos. Código e resultados técnicos foram preservados. As evidências anteriores foram mantidas.

Os arquivos usam extensão .ipynb.json para preservar outputs no Git. Para abrir como notebook, baixe e remova apenas o sufixo .json. O commit dos notebooks ativos continuava sem outputs na revisão; estes exports são a cópia arquivada da coleta.
