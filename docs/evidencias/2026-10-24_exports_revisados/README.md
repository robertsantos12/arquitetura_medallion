# Evidências 00 e 01 — cópias revisadas para publicação

Publicação autorizada pelo responsável no repositório robertsantos12/arquitetura_medallion, com remoção de e-mail e caminhos pessoais.

As cópias preservam o código das células e os outputs técnicos. Metadados do Databricks foram removidos, e o caminho pessoal exibido pelo notebook 01 foi substituído por [CAMINHO_PESSOAL_REMOVIDO]. O manifesto discrimina os hashes dos arquivos recebidos e publicados e as alterações. Estas cópias não são os bytes originais.

| Notebook | Resultado verificado nos exports |
| --- | --- |
| 00 | Delta, MERGE, releitura e repetição para id=1 aprovados |
| 01 | Pacote importado e cinco schemas dev disponíveis |

Os arquivos usam a extensão adicional .json para serem tratados como arquivos comuns pela pasta Git, preservando os outputs fora do mecanismo de conversão de notebooks. Para reimportar uma cópia no Databricks, baixe e remova apenas o sufixo .json.

Os módulos importados na execução original não tinham snapshot; os exports não comprovam sozinhos a versão desses módulos. O horário de preparação do manifesto não é horário de execução. Hashes ajudam a detectar alterações em relação ao manifesto e não são assinatura de autenticidade.
