# Preservação de notebooks executados

## Padrão adotado

O arquivo `.databricks/commit_outputs` está configurado para solicitar a inclusão de outputs dos notebooks em `notebooks/` e de `teste_ambiente.ipynb`, quando presente. A inclusão efetiva precisa ser verificada no arquivo remoto. Cada commit de evidência é um checkpoint: execuções que ocorrem entre commits não ficam arquivadas automaticamente. Esta configuração também não cria um histórico Delta de execuções ou armazena logs internos do cluster.

A configuração do repositório depende de habilitação no workspace. A implementação só estará validada quando um commit feito no Databricks contiver outputs reais e for conferido no GitHub.

## Habilitação no workspace

Conforme a documentação do Databricks:

1. Abra o menu do usuário → Settings.
2. Em Workspace admin, abra Development.
3. Na seção Repos, habilite **Allow repos to export IPYNB output** com **Allow: IPYNB outputs can be toggled on**.

Os nomes podem variar conforme idioma/versão. Se não houver a opção, confirme se a conta é administradora e se o workspace oferece esse controle; não considere a persistência habilitada apenas pelo arquivo no Git.

Fonte: https://docs.databricks.com/aws/en/notebooks/notebook-format

## Incidente confirmado em 24/10/2026

A interface mostra included e outputs do notebook 00, mas os blobs de 00 e 01 no commit 8eb90b2 têm outputs vazios. O hash dos bytes foi conferido. Não repetir habilitação ou reexecução sem preservar o estado atual. Primeiro exportar os dois notebooks com Include outputs e conferir os arquivos. Consulte [a investigação e o desenho proposto](rastreabilidade_execucoes.md).

## Procedimento geral de commit (retomar após resolver a divergência)

1. Habilite a opção do workspace.
2. Na pasta Git, confirme a branch `chore/estrutura-inicial` e faça Pull para receber a configuração.
3. Abra `notebooks/00_validar_delta.ipynb`. Em **File → Commit notebook outputs**, confirme **Include Outputs**, caso o menu esteja disponível.
4. Execute **Run all**. Não limpe as saídas.
5. Abra o diálogo Git, confira as alterações do notebook e faça commit/push com `docs: registra execucao Delta com outputs`.
6. Confira no GitHub o notebook desse commit. As células executadas devem conter os resultados reais, incluindo `VALIDAÇÃO DELTA: OK`. Um contador de execução sozinho não comprova que os outputs foram incluídos.
7. Repita o processo para `notebooks/01_preparar_projeto.ipynb`, com o commit `docs: registra preparacao do projeto com outputs`.
8. Só avance após confirmar que os resultados chegaram ao GitHub.

Se existirem alterações locais que impeçam o Pull, preserve o notebook atual exportando em IPYNB com **Include outputs** antes de resolver o conflito. Não descarte resultados sem preservá-los.

O teste Delta e o bootstrap foram desenhados para serem repetidos. Se uma execução falhar, preserve o erro em um commit próprio quando ele for relevante à validação; registre a correção e a nova execução em commits seguintes.

## Procedimento para cada etapa

Execute todas as células na ordem, confira as verificações finais, revise os outputs e faça commit/push. Depois confirme a presença das saídas no GitHub. Registre em `docs/evidencias.md` a etapa, o commit e o resultado observado. Nunca preencha outputs manualmente para representar uma execução.

O notebook no estado atual guarda os resultados mais recentes; os commits anteriores preservam os checkpoints anteriores. Uma alteração posterior no código exige nova execução para que o resultado corresponda ao código entregue.

## Se o workspace não oferecer commit de outputs

Use **File → Export → IPython notebook**, habilitando **Include outputs**. Guarde o arquivo executado em `docs/evidencias/etapa_XX/<timestamp_UTC>_<nome>.ipynb` e versione esse arquivo. HTML com outputs pode ser usado como cópia de leitura quando o ambiente permitir seu versionamento; IPYNB é a evidência canônica.

Esta é a rota imediata de recuperação enquanto a divergência entre workspace e GitHub estiver aberta. A cópia deve ser conferida antes de ser aceita como evidência.

Fonte: https://docs.databricks.com/aws/en/notebooks/notebook-export-import

## Limites e escopo

São preservados os outputs que o Databricks incluiu no notebook, sujeitos aos limites de tamanho da plataforma. Dados completos devem ser gravados em Delta/arquivos pelo pipeline, em vez de depender de uma exibição de tabela. Apenas dados sintéticos e resultados apropriados ao repositório devem compor a evidência.

O histórico operacional persistente de execuções, com batch_id, status, tempos e contagens, será implementado com o pipeline. Ele complementará as evidências dos notebooks; ainda não existe nesta etapa.
