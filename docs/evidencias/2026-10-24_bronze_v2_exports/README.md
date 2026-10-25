# Arquivamento das evidências — Etapa 05 Bronze V2

Data do registro: 24/10/2026. Branch: `chore/estrutura-inicial`.

Quatro exports IPYNB fornecidos pelo responsável e publicados individualmente, **com outputs**, no GitHub. O conteúdo JSON foi reserializado pelo mecanismo de leitura do anexo para arquivamento; portanto, o byte-a-byte do arquivo versionado pode diferir do export original, embora células, metadados e resultados tenham sido preservados. Os hashes SHA-256 abaixo referem-se aos **arquivos originais recebidos**, não ao conteúdo reserializado no GitHub. Para conferir integridade do versionamento, os blob SHAs Git constam na tabela.

| Execução | Arquivo versionado | SHA256 do export original | SHA blob no Git |
| --- | --- | --- | --- |
| Lote 01 inicial | [05_ingerir_bronze_v2-lote_01_inicial.ipynb](05_ingerir_bronze_v2-lote_01_inicial.ipynb) | `d74927b7cff1a053ce7eb51448170993fc32431db043b26bbb9b87a5b5d27c0f` | `cdfead12a26066b5edee4019f4a65b9a62fb6084` |
| Repetição lote 01 | [05_ingerir_bronze_v2-lote_01_inicial-repetido.ipynb](05_ingerir_bronze_v2-lote_01_inicial-repetido.ipynb) | `7d462b35a493876acd50189849c67aae7ee1e78f90a713c1d6ded8ff37c3cc27` | `33b8f2d446f6b1430e78731c81767134bddbcea8` |
| Lote 02 incremental | [05_ingerir_bronze_v2-lote_02_incremental.ipynb](05_ingerir_bronze_v2-lote_02_incremental.ipynb) | `b490fbb3adc40ad70b334724a98f349bcf52b3f72b5e25d04fef74076d4904ae` | `43cb32424f412a08806bfb3f289f09736826ae8c` |
| Lote 03 atrasado | [05_ingerir_bronze_v2-lote_03_atrasado.ipynb](05_ingerir_bronze_v2-lote_03_atrasado.ipynb) | `2318ed41044b2220c0b853174be9902124ddff02aae95dab2ce8c422cdd020a8` | `a14b3fac28a3d3330077793e9324f5c91cb9e87c` |

## Resultados observados

Todos os quatro exports apresentam `BRONZE V2: OK`, cinco blocos de output por notebook e nenhuma saída do tipo `error`.

| Lote | Transações esperadas e registradas na Bronze |
| --- | ---: |
| 01_inicial | 6.080 |
| 02_incremental | 4.560 |
| 03_atrasado | 1.518 |
| **Total** | **12.158** |

A repetição de `01_inicial` manteve **6.080** registros nesse lote e **12.158** no total após todos os três lotes já carregados, de acordo com a saída do notebook repetido.

O export do teste de repetição foi produzido após os demais lotes, como mostram os dados de contagem exibidos nele. A evidência confirma **contagens invariáveis** na repetição; a verificação de ausência de inserções duplicadas por chave também depende da lógica MERGE versionada, não apenas das contagens.

## Escopo

Validação funcional **baseada nos quatro notebooks executados e enviados**, sem acesso independente ao estado atual do workspace. Bronze V2 aprovada para esta rodada, sujeita a melhorias adicionais solicitadas antes de iniciar a Silver. Não há merge em `develop` ou `main`. Nenhum dado real de cliente foi utilizado: a origem é sintética.
