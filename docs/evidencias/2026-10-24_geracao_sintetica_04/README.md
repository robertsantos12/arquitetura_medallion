# Evidência da geração sintética — notebook 04

Export enviado pelo operador: DADOS SINTÉTICOS: OK. Lotes 01/02/03 têm 21/12/3 registros, respectivamente (36 no total). Foram publicados 17 arquivos de dados e um manifesto; zero arquivos reutilizados na primeira chamada. A repetição interna sem novas gravações foi aprovada pela auditoria: INICIADA, cinco VERIFICACAO e SUCESSO, com sete eventos e hashes verificados.

Manifesto do cenário e snapshot das fontes Python/pyproject foram reconstruídos localmente e seus hashes conferem com os outputs. Não houve consulta direta ao Delta/Volume pelo revisor. O export mostra os resumos e resultados de verificação, não todos os JSON de evidência do Volume.

O export preserva a célula de reinício do Python adicionada pelo operador. Essa célula foi removida apenas do notebook ativo após a coleta, para restabelecer widgets no primeiro CMD. Os demais códigos de execução permanecem iguais. O reinício observado no código não fornece telemetria independente de sua execução.

A cópia pública remove metadados Databricks e eventuais e-mails/caminhos pessoais, preservando resultados técnicos. O manifesto registra hashes do upload original e da cópia publicada. Remova somente .json de .ipynb.json para abrir como notebook. Esta etapa valida geração e persistência; Bronze/Prata/Ouro seguem pendentes.
