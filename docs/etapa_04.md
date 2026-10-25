# Executar somente 04_gerar_dados_sinteticos

Pré-requisitos: notebooks 00–03 validados, Pull da branch `chore/estrutura-inicial`, permissão CREATE VOLUME no schema landing e READ/WRITE VOLUME. O notebook usa o driver Python para a fixture pequena, com escrita sequencial de arquivos completos, compatível com as restrições de Volumes (sem append aleatório). Referência: https://docs.databricks.com/aws/en/volumes/volume-files.

1. Se o pacote já foi importado, reinicie o processo Python antes de começar. Não mantenha uma célula de reinício dentro de Run all.
2. Execute somente o primeiro CMD para exibir os widgets.
3. Informe catalogo=workspace, data_referencia=2026-01-15 e batch_id vazio. A data é a base fixa dos eventos de teste, não a data de execução. O batch vazio gera um identificador; não copie o UUID de volta para o widget.
4. Execute os CMDs seguintes em ordem. O CMD 3 mostra os parâmetros; o CMD 4 gera, relê e verifica repetição. Esperado: DADOS SINTÉTICOS: OK e auditoria SUCESSO com hashes verificados.
5. Exporte IPYNB com outputs, confira o arquivo e faça commit/push. Envie export e SHA para revisão antes da Bronze.

O manifesto é escrito por último e só existe após a preparação dos dados; consumidores também devem validar todos os hashes, pois o manifesto não é uma transação multiarquivo. Repetição compara bytes, reutiliza arquivos iguais e interrompe em divergência. Falhas parciais podem ser retomadas com os mesmos parâmetros; não apagar evidências. Não execute dois escritores simultaneamente para a mesma data/cenário: a comparação de existência não é um lock distribuído. O agendamento futuro deve limitar concorrência a 1. Para alterar os dados do cenário, criar nova versão em vez de sobrescrever v1.

O código registra fontes, contexto, hashes/contagens dos arquivos e cinco verificações no AuditRun. O snapshot cobre os módulos Python e pyproject; o notebook executado é coletado por export separado. Criação inicial da infraestrutura de auditoria ainda precede o AuditRun; falhas nessa preparação propagam e precisam do output do notebook. Falhas posteriores registram FALHOU quando o armazenamento de auditoria estiver disponível. Não existe atomicidade entre os arquivos de entrada e a auditoria.

O gerador prepara os três lotes agora. Não carregar a pasta inteira na primeira execução da Bronze: consumir 01_inicial, depois 02_incremental e por último 03_atrasado, para demonstrar chegada fora de ordem. Esta etapa não implementa ingestão Bronze, SCD2 ou métricas Ouro. Veja data_contracts.md para cenários e oráculos previstos.

## Verificação antes da execução Databricks

`PYTHONPATH=src python3 -m unittest discover -s tests -v`: 21 testes aprovados (17 anteriores e 4 novos). Novos testes cobrem contratos/serialização, cenários temporais e financeiros da fixture, repetição sem regravar, retomada sem manifesto, corrupção e arquivo inesperado. Sintaxe dos módulos e quatro CMDs verificada. Essa validação local não substitui a execução no Volume/Delta do Databricks, ainda pendente de coleta.
