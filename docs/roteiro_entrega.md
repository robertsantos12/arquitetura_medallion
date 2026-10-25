# Passo a passo de revisão, integração e entrega

## 1. Congelar a validação

Fazer Pull de chore/estrutura-inicial. Não regenerar dados nem reexecutar 00–08/10/11. 09 após metadados já passou e está arquivado; não repetir sem mudança de dados/regras. Ler matriz_requisitos_pdf.md e backlog_v2.md. Manter 12 como bloqueado por permissão, sem tentar contornar privilégios.

## 2. Resolver a decisão de aderência antes de aprovar main

A Bronze ainda não expõe integralmente batch_id, hash_linha e schema_version conforme o PDF. Não tratá-los como requisito opcional. Preferir complemento compatível com testes (por exemplo, view contratual com batch por vínculo auditado, hash do payload e versão do manifesto), sem sobrescrever baseline. Até implementar e validar, registrar PARCIAL no PR; não aprovar dizendo que tudo foi cumprido. View contratual precisa ter semântica exata, não renomear run_id como batch_id nem hash posicional como hash de conteúdo.

Revisar todos os arquivos do pacote por segredos, emails e caminhos pessoais, incluindo exports antigos. Exports novos sanitizados não garantem limpeza dos anteriores nem do histórico Git. Preservar originais e fazer cópia revisada de entrega; não reescrever histórico nem apagar evidências automaticamente.

## 3. Abrir PR de revisão para develop

No GitHub, Pull requests → New pull request. Selecionar base=develop e compare=chore/estrutura-inicial. Confirmar direção antes de criar. Título sugerido: `feat: entrega Lakehouse NovaRota com evidências de homologação`.

Descrição deve conter: escopo Bronze/Silver/Gold/SQL; referência à matriz; 09 final após metadados; validações 10/11; testes locais; limitações do driver/snapshots; metadados Bronze parciais; linhagem 12 bloqueada; nenhum deploy prod. Criar como Draft enquanto houver ações de fechamento. Não incluir credenciais ou dados pessoais na descrição.

Revisar Files changed e Commits, comparar com evidências e confirmar ausência de alterações destrutivas. Rodar testes da versão congelada: `PYTHONPATH=src python3 -m unittest discover -s tests -v`. Houve 40 testes aprovados no fechamento local de 25/10; registrar novo resultado se o código mudar.

## 4. Aprovar e integrar develop

Somente após revisão do PR e decisão explícita sobre pendências. Se permanecer uma lacuna obrigatória, manter o parecer parcial visível e priorizar correção; não ocultar no backlog. Preferir Create a merge commit para preservar o histórico incremental exigido no PDF. Evitar squash do trabalho inteiro. Não apagar chore até encerrar entrega/retomadas. Não resolver conflito pelo botão sem revisar alterações.

## 5. PR de release develop → main

Após develop integrado e revisado, criar novo PR com base=main, compare=develop. Vincular PR anterior, SHA aprovado, testes/evidências e notas de release. Revisar, aprovar e fazer merge somente quando autorizado pelo responsável. Não executar automaticamente porque o PR foi criado. Atualizar pasta Git do Databricks apenas para a branch desejada após salvar outputs.

## 6. Empacotar a entrega privada

Após definir o SHA de release, gerar ZIP a partir desse SHA, com código, pyproject, SQL, notebooks, documentação e evidências revisadas. Incluir manifesto de arquivos/hashes, SHA da release e instruções de execução. Excluir caches e credenciais; não incluir arquivos brutos pessoais apenas porque estão em diretório de evidência. Validar conteúdo extraído e testes. O ZIP ainda não foi produzido. Alternativa é repositório privado; visibilidade só deve ser alterada por decisão explícita do proprietário.

## 7. Defesa técnica

Explicar o caminho arquivos→Bronze→SCD2/qualidade→Gold→SQL; diferença entre data_referencia e data_corte; por que 12.158 linhas Bronze viram 12.153 transações válidas; por que oito inválidos abrangem todas as fontes; por que o oráculo 2270 é só V1; PK informativa e snapshot_id; recusas e chargeback sem gasto duplicado; limites da fixture/driver; decisões de não particionar; streaming como evolução e linhagem bloqueada. Uso de IA é permitido pelo PDF, mas o candidato precisa defender as decisões.

Merge em main é promoção de código. Não cria um ambiente produtivo: catálogo/schemas utilizados continuam dev, com dados sintéticos. Uma implantação prod requer configuração, permissões, operação e validação próprias.
