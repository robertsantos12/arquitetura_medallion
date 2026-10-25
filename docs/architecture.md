# Arquitetura e escopo

## Fluxo planejado

Arquivos sintéticos → Landing em Unity Catalog Volume → Bronze Delta → Prata Delta → Ouro Delta.

O catálogo dev é `workspace`, confirmado pela validação do responsável. Para esta demonstração, os ambientes são separados pelo nome dos schemas; isso organiza objetos, mas não substitui permissões. Em produção, catálogos por ambiente e grants por identidade precisam ser definidos conforme a plataforma.

| Schema dev | Finalidade planejada |
| --- | --- |
| `medallion_dev_landing` | Volume com arquivos de entrada e checkpoints |
| `medallion_dev_bronze` | Dados brutos e metadados de ingestão |
| `medallion_dev_prata` | Dados tipados, histórico e quarentena |
| `medallion_dev_ouro` | Produtos analíticos e features |
| `medallion_dev_controle` | Execuções, arquivos processados e métricas operacionais |

Nesta entrega, o bootstrap prepara somente os schemas. A disponibilidade de Volumes e checkpoints ainda será validada. A estratégia de ingestão incremental, recuperação de falhas e evolução de schema será implementada e documentada na etapa Bronze.

## Organização de código

Notebooks recebem parâmetros e chamam funções do pacote `medallion`. Configuração não depende de Spark; funções com operações distribuídas recebem a sessão Spark explicitamente. Regras de negócio e qualidade terão módulos próprios quando forem implementadas. Logs JSON usam UTC e batch_id.

## Validação por etapa

Testes locais cobrem código Python independente de Spark. A validação no Databricks cobre integração real com Unity Catalog e Delta. Testes com mocks não comprovam execução Spark. Cada etapa deve registrar o que foi executado, o resultado e as limitações, sem registrar credenciais ou dados reais.


## Atualização — preparação para homologação

Silver e Gold de homologação implementadas em módulos com snapshots Delta insert-only, marcador de completude e filtro obrigatório snapshot_id. Fonte Bronze permanece imutável nesta revisão. Ver homologacao_domingo.md para grãos, UTC, operação e limites do driver.
