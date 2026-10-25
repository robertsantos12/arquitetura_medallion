# Rastreabilidade de execuções — investigação de 24/10/2026

## Conclusão

A interface do Databricks e o GitHub têm estados diferentes neste momento. O print do notebook 00 mostra execução bem-sucedida, Spark 4.2.0, catálogo workspace e a opção de commit de outputs como included. Isso comprova o resultado visível no workspace, mas não seu arquivamento no GitHub.

No commit `8eb90b2a78304b7661146e3a123cf948ed43ca4b`, as duas células de código do 00 e as três do 01 têm outputs vazios. Os arquivos foram consultados por conteúdo e por blob. O hash Git dos bytes recebidos foi recalculado (SHA-1 do cabeçalho blob e do conteúdo) e coincide com os identificadores do GitHub:

| Notebook | Blob SHA confirmado | Células com outputs |
| --- | --- | ---: |
| 00_validar_delta | bfee64591880d3de22dd08865e50d07dbbee16c5 | 0 |
| 01_preparar_projeto | 555b9453eeb38c4e27754f6bf2fe89baad5fa5e1 | 0 |

Isso elimina a hipótese de os resultados terem sido removidos apenas pela leitura do conector nessa consulta. A causa no caminho de exportação/commit do Databricks continua não determinada. Os prints não mostram o diff nem o instante em que a opção foi habilitada em relação aos commits. Não há evidência suficiente para atribuir a falha ao usuário, ao serverless ou a um bug específico.

## Persistência e limites documentados

| Objeto | O que a documentação permite concluir |
| --- | --- |
| Memória e disco temporário do serverless | São efêmeros e não servem como arquivo de evidências. |
| Resultados interativos salvos | Ficam no armazenamento gerenciado do workspace/control plane, conforme o tipo de workspace; são distintos do disco temporário do compute. |
| Resultados visíveis em um notebook | Podem ser limpos ou substituídos por outras execuções. Não equivalem a um arquivo de todas as tentativas. |
| Histórico de Jobs | Retenção documentada de 60 dias. Resultados necessários por mais tempo devem ser exportados. |
| Outputs de células | Estão sujeitos a limites de tamanho e truncamento; tabelas exibidas não representam necessariamente todos os dados. |
| Logs no serverless | Spark logs e Spark UI não estão disponíveis; há logs de aplicação no cliente e query profile. |

Inferência operacional: terminar o compute não equivale a apagar automaticamente os outputs já persistidos do notebook. Não foi localizada uma garantia geral de prazo de retenção dos outputs interativos que permita prometer armazenamento permanente no workspace deste projeto. O prazo de 60 dias se refere a Jobs, não deve ser aplicado automaticamente a notebooks interativos.

Fontes:
- [Armazenamento e ciclo de vida no serverless](https://docs.databricks.com/aws/en/security/keys/customer-managed-keys)
- [Resultados e limpeza de estado](https://docs.databricks.com/aws/en/notebooks/notebook-outputs)
- [Retenção e exportação de Jobs](https://docs.databricks.com/aws/en/jobs/monitor)
- [Limites dos notebooks](https://docs.databricks.com/aws/en/notebooks/notebook-limitations)
- [Limitações de logging no serverless](https://docs.databricks.com/aws/en/compute/serverless/limitations)

## Preservação imediata

Antes de alterar código, limpar resultados, executar de novo ou sincronizar a pasta Git:

1. Exportar 00 e 01 em IPython notebook (.ipynb), com Include outputs.
2. Validar o JSON de cada arquivo: presença dos outputs, erros, verificações finais e correspondência entre o código exportado e o código versionado.
3. Arquivar os bytes exportados em uma pasta por captura em `docs/evidencias/`, junto de um manifesto. O horário da captura não deve ser apresentado como horário original da execução.
4. Registrar SHA-256 do arquivo, notebook de origem, commit de código comparado, resultado da verificação e limitações da evidência. Nunca inventar horários, run_id ou checks ausentes.
5. Versionar os arquivos já verificados e conferir a cópia remota. Para esta recuperação, usar upload direto ao GitHub fora da conversão da pasta Git do Databricks.

O arquivo exportado permite investigar o defeito: se contém resultados, a divergência está no caminho de commit; se também está vazio, investigar a exportação/persistência do notebook. Em ambos os casos, preservar a cópia disponível antes de outra tentativa.

[Documentação de exportação com outputs](https://docs.databricks.com/aws/en/notebooks/notebook-export-import).
[Configuração de commit de outputs](https://docs.databricks.com/aws/en/notebooks/notebook-format).

## Desenho proposto para as próximas execuções

Status: proposta de implementação, não implantada.

| Componente | Registro proposto | Papel |
| --- | --- | --- |
| Git | Código, testes, decisões, revisão e amostras de evidências verificadas | Identificar a versão revisada |
| Tabela Delta de controle | Eventos por run_id e tentativa, batch_id, etapa, tempos UTC, status, parâmetros, commit/hash de código, contagens e checks | Consultar o histórico operacional |
| Unity Catalog Volume | JSON do manifesto, logs de aplicação, exportação do notebook quando disponível e hashes dos artefatos | Preservar arquivos independentemente do compute |
| Jobs | Identificadores e estado da execução; exportação posterior por coletor | Executar de forma reproduzível e reconciliar interrupções |

Volumes são objetos de armazenamento em nuvem adequados a arquivos e logs. A existência e as permissões no workspace ainda precisam ser validadas: [Unity Catalog Volumes](https://docs.databricks.com/aws/en/volumes/).

Cada tentativa recebe um run_id novo; batch_id pode ser repetido para o mesmo lote. Registrar início antes do processamento e conclusão somente após checks e persistência das evidências. Exceções devem preservar o erro e ser propagadas. Uma interrupção abrupta pode impedir a gravação final: execução sem conclusão deve permanecer INCOMPLETA até reconciliação, nunca ser promovida a sucesso por ausência de erro.

A implementação deve separar resultado do processamento e estado do arquivamento. Um pipeline que terminou com sucesso mas falhou em salvar evidências não passa pelo aceite da etapa. O coletor posterior deve tratar sucesso, falha e cancelamento; um bloco finally sozinho não cobre morte do processo.

Para Jobs, exportar o notebook renderizado pelo mecanismo de exportação de runs. A API get-output não é um coletor geral de todos os prints de notebook: o campo notebook_output retorna o valor de dbutils.notebook.exit, com limite de 5 MB, e o campo logs não é suportado para notebook_task. Referências: [export-run](https://docs.databricks.com/api/jobs/v2/export-run) e [get-run-output](https://docs.databricks.com/api/jobs/v2/get-run-output).

## Critérios de aceite e uso de IA

- Código proposto pela IA deve estar associado à versão executada, aos testes e à revisão humana.
- Uma mensagem de sucesso precisa corresponder a verificações executadas; não substituir checks por texto manual.
- Evidências de falha também devem ser registradas. Nova tentativa não sobrescreve a anterior.
- Comparar comportamento esperado e observado, incluindo idempotência e contagens quando aplicável.
- Verificar leitura das evidências a partir de nova sessão, após salvar em armazenamento persistente.
- SHA-256 detecta alteração em relação ao manifesto; não é assinatura de autoria nem prova isolada de execução.
- Tabelas e arquivos com permissão de alteração não são imutáveis. Retenção, permissões e backup precisam ser definidos e testados; Git não deve ser o único arquivo operacional.
- Garantia coberta: execuções do pipeline instrumentado. Células exploratórias avulsas não serão capturadas automaticamente por esse desenho.

Antes da massa sintética, validar a exportação de 00/01 e implementar uma prova pequena de persistência: sucesso, erro controlado, repetição com run_id diferente e releitura em nova sessão. O teste de erro deve ser identificado como teste controlado.
