# Etapa 2B — Registro persistente por tentativa

## Executar

1. Faça Pull em chore/estrutura-inicial.
2. Execute notebooks/02_validar_rastreabilidade.ipynb com catálogo workspace e batch_id vazio.
3. Aguarde RASTREABILIDADE: OK e guarde a lista RUN_IDS_PARA_RELEITURA.
4. Abra notebooks/03_reler_evidencias.ipynb em uma nova sessão Python, informe a lista no widget run_ids e execute.
5. Espere RELEITURA DAS EVIDÊNCIAS: OK. Se a sessão for reutilizada, registre essa limitação; ainda falta testar em nova sessão.

O teste 02 gera duas tentativas de sucesso do mesmo lote e uma falha proposital. Os resultados esperados são SUCESSO, SUCESSO, FALHOU. Somente o AssertionError deliberado é esperado; falhas de criação de Volume, permissões e gravação propagam e interrompem o notebook.

## Objetos de desenvolvimento

| Objeto | Nome |
| --- | --- |
| Tabela Delta | workspace.medallion_dev_controle.execucoes_eventos |
| Volume gerenciado | workspace.medallion_dev_controle.evidencias |
| Pasta por tentativa | /Volumes/workspace/medallion_dev_controle/evidencias/execucoes/<run_id>/ |

O 02 cria os objetos com IF NOT EXISTS. O 03 é somente leitura e não chama preparação. A conta executora precisa poder criar e usar os objetos. O suporte a Volumes será validado nesta execução.

## Arquivos e eventos

Cada tentativa recebe run_id UUID novo. Batch_id identifica o lote e pode ser reutilizado. São gravados fontes.json (snapshot dos módulos Python e pyproject), contexto.json (parâmetros, runtime e hash do código) e um arquivo JSON por evento. Os arquivos são escritos de forma sequencial, com fechamento e releitura imediata; não é usado append de arquivo, operação não suportada diretamente por Volumes.

Cada evento tem timestamp UTC, etapa, status, parâmetros, verificações ou erro, referência aos arquivos anteriores e hashes SHA-256. A tabela guarda uma cópia JSON do evento e o hash do arquivo correspondente. Não há captura automática de todos os prints, displays ou logs internos do Spark; o conteúdo capturado é o registro estruturado da execução instrumentada.

Fontes técnicas: [Volumes](https://docs.databricks.com/aws/en/volumes/) e [limitações de escrita em arquivos](https://docs.databricks.com/aws/en/volumes/volume-files).

## Falhas e integridade

Gravação do arquivo e append Delta não formam uma transação única. Se um lado falhar, a função levanta AuditPersistenceError. Arquivos parciais podem permanecer e exigem reconciliação. Um erro de processamento é registrado com traceback e propagado; falha na gravação do erro preserva a exceção original como causa.

Verificações malsucedidas não geram SUCESSO. Uma tentativa sem verificações também é rejeitada. Se o processo for encerrado abruptamente, pode restar INICIADA sem conclusão: a consulta retorna SEM_CONCLUSAO, sem concluir automaticamente que falhou ou ainda está em execução. Reconciliação automática com Jobs ainda não está implementada.

A releitura confere hashes dos eventos, contexto e fontes, igualdade entre Delta e arquivos, identificadores, sequência e estados terminais. Detecta registros duplicados e lacunas observáveis; uma sequência sem evento terminal não é aceita como sucesso. O verificador não prova autenticidade contra um administrador capaz de alterar tabela, arquivos e hashes juntos.

## Versão executada e limitações

O snapshot preserva arquivos Python e pyproject lidos no início, não o conteúdo da memória do interpretador. Após alterar módulos, use uma nova sessão Python para não misturar código em cache com arquivos novos. O notebook de execução é uma camada fina; a prova é implementada no módulo observability.proof.

A vinculação automática a um commit Git verificado, exportação automática do notebook, coleta de toda execução exploratória, identidades de Jobs, retenção automática, políticas de acesso e backup não estão implementadas. Essas capacidades serão acrescentadas com a orquestração. Não se afirma imutabilidade/WORM.

O desenho é voltado a eventos por etapa, não por registro de negócio. A prova usa poucos arquivos e pequenos appends Delta; volume e otimização serão tratados antes de escalar.

## Situação de aceite

17 testes locais passaram. Integração real com Databricks ainda pendente. Avançar para dados sintéticos depois de confirmar escrita e releitura persistentes, incluindo uma nova sessão.
