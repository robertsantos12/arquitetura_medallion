# Início do projeto

## Estado atual

Acesso ao GitHub validado. Pipeline ainda não implementado e execução no Databricks ainda não validada.

## Etapas iniciais

1. Preparar repositório e branch de trabalho.
2. Identificar modalidade do Databricks, compute e catálogo/schema ou caminho disponível; executar leitura e escrita Delta em área de teste.
3. Aprovar contratos: valor de estorno, status transacional, ordenação CDC e vigência de negócio.
4. Implementar massa mínima e primeiro fluxo Bronze → Prata → Ouro.

## Divisão de responsabilidades

A IA prepara estrutura, configurações, gerador, implementação das regras aprovadas, testes e documentação. Cada entrega deve indicar mudanças, validação realizada e limitações.

O responsável sênior aprova semântica financeira, histórico, rejeições e modelagem; revisa resultados e integração na main.

## Organização prevista

- src/medallion/: módulos do pipeline, criados conforme implementação.
- notebooks/: execução e diagnóstico do ambiente.
- tests/: testes com resultados conhecidos.
- sql/: consultas analíticas.
- scripts/: gerador de massa fictícia.
- docs/: contratos, decisões e instruções.

## Próxima informação necessária

Modalidade do Databricks (Free Edition, ambiente corporativo ou outra) e existência de workspace com execução disponível. Não registrar tokens ou senhas no repositório.
