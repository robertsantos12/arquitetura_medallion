# Preservação de execuções

## Padrão atual

1. Código, testes e decisões ficam no Git.
2. Execuções instrumentadas pela camada de auditoria gravam eventos Delta e evidências JSON em Volume.
3. Exportações com outputs comprovam o conteúdo visual de notebooks quando necessário.
4. O aceite exige conferir o artefato gravado, e não apenas a mensagem exibida.

O mecanismo de auditoria está implementado, mas aguarda validação real com os notebooks 02 e 03. Veja [instruções e limitações](rastreabilidade_implementacao.md).

## Exports iniciais 00 e 01

Os exports recebidos foram verificados: ambos contêm resultados e código correspondente ao repositório. Sua publicação integral ainda está pendente. A exportação preservou os outputs; o caminho de commit da pasta Git enviou arquivos vazios anteriormente. A causa exata continua indeterminada.

Ao recuperar evidências, exporte antes de reexecutar, limpar resultados ou sincronizar alterações. Use File → Export → IPython notebook, marcando Include outputs. Preserve os bytes originais e registre hash, origem e momento da captura, sem confundir captura e execução. Qualquer remoção de metadados precisa estar explícita no manifesto da cópia publicada.

## Commit de outputs

.databricks/commit_outputs continua configurado para notebooks/ e teste_ambiente.ipynb. Essa configuração solicita inclusão de outputs; somente a conferência do arquivo remoto comprova que foram enviados. Não depender desse caminho como único arquivo operacional.

Uma evidência JSON tratada como arquivo comum evita depender da conversão de notebooks da pasta Git. Ao arquivar um export com extensão adicional .json, seus bytes podem permanecer idênticos; para reimportar uma cópia como notebook, remova apenas esse sufixo. O formato exato da publicação dos exports iniciais ainda está pendente.

## Procedimento de aceite

Confirmar checks e status, conferir arquivos e tabela, verificar hashes, associar código e parâmetros e registrar a revisão. Falhas de processamento e de arquivamento são resultados diferentes e ambos precisam ser visíveis. Não sobrescrever tentativas anteriores nem reconstruir outputs manualmente para aparentar execução.

Execuções avulsas fora do código instrumentado precisam de exportação explícita. O histórico nativo do workspace não é o arquivo definitivo do projeto.

Referências:
- [Exportação](https://docs.databricks.com/aws/en/notebooks/notebook-export-import)
- [Commit de outputs](https://docs.databricks.com/aws/en/notebooks/notebook-format)
- [Investigação inicial](rastreabilidade_execucoes.md)
