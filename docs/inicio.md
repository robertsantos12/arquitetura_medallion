# Início do projeto

## Estado atual

GitHub e Databricks conectados. Escrita e leitura Delta, MERGE e repetição sem duplicidade para a chave de teste foram validados pelo responsável no Databricks. Veja `evidencias.md`.

Etapa atual: estrutura modular, configuração, logs e preparação dos schemas dev. Execute `notebooks/01_preparar_projeto.ipynb` conforme o README e valide antes da geração de dados.

## Divisão de responsabilidades

A IA prepara código, testes, documentação e commits na branch de trabalho. O responsável executa no workspace, revisa resultados e aprova regras financeiras e integração. Logs e falhas devem ser compartilhados sem tokens ou senhas.

## Próxima etapa

Validar suporte e acesso a Unity Catalog Volumes, definir contratos e criar uma massa sintética pequena e determinística. Depois implementar o primeiro fluxo Bronze → Prata → Ouro, preservando evolução incremental no Git.
