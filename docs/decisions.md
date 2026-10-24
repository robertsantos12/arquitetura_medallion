# Decisões técnicas

## ADR-001 — Pacote Python e notebooks de execução

Status: adotado na etapa 2.

O desafio pede código modular e reproduzível. Usamos layout `src/medallion`, parâmetros explícitos e notebooks curtos. Durante desenvolvimento, o notebook localiza `src` na pasta Git e importa o pacote sem instalação de dependências. Para execução agendada em produção, o empacotamento em wheel e a implantação por Jobs serão definidos após o pipeline funcional.

Trade-off: executar diretamente da pasta Git é simples neste estágio, mas não substitui um artefato versionado para implantação. O pyproject permite empacotar o mesmo código posteriormente.

## ADR-002 — Schemas separados por ambiente e camada

Status: adotado para desenvolvimento.

Usamos o catálogo `workspace` já validado e schemas `medallion_dev_*`. O schema `medallion_dev_setup` fica reservado ao diagnóstico Delta da etapa 1. O bootstrap só aceita dev, não altera grants e preserva objetos existentes.

Trade-off: a separação por nome evita misturar camadas, porém o isolamento de segurança dependerá de grants e identidades. A configuração aceita nomes de ambiente futuros; provisionamento de hml/prod não está implementado.

## ADR-003 — Massa sintética e contratos antes da ingestão

Status: planejado, pendente da próxima etapa.

O gerador será determinístico, com duplicidades, CDC fora de ordem, dados atrasados e registros inválidos. Não usaremos dados reais. Precisamos explicitar valor de estorno parcial, status transacional e critério de desempate CDC antes de gerar cenários com resultados esperados. Campos adicionais devem ser documentados como extensão do contrato do desafio.

## Decisões ainda pendentes

Auto Loader versus alternativa compatível com o ambiente; controle incremental e recuperação de falhas; deduplicação entre lotes; SCD2 com alterações retroativas; joins temporais; métricas financeiras; estratégia de clustering; Workflows e CI. Estes pontos não estão implementados nesta entrega.
