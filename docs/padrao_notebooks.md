# Padrão dos notebooks de execução

A primeira célula executável declara todos os widgets necessários. Ela deve funcionar sem importar o pacote do projeto e sem ler os valores preenchidos, validar parâmetros ou executar operações de negócio.

Fluxo interativo:

1. Executar apenas a primeira célula de código para exibir os campos.
2. Preencher os widgets.
3. Executar as células seguintes, que importam os módulos, leem os valores, validam e executam.

Run all pode ser usado quando os parâmetros já estiverem preenchidos, inclusive em uma execução automatizada com parâmetros fornecidos previamente. Run all não pausa para o preenchimento manual dos campos.

Novos notebooks devem seguir a mesma separação. A declaração de widgets não deve ficar junto do código que consome seus valores. Não remover e recriar widgets com removeAll durante a preparação dos campos, para preservar valores já definidos.

Os notebooks 00, 01, 02 e 03 foram ajustados. Seus resultados anteriores continuam documentados nas evidências; a reorganização das células não deve ser apresentada como nova execução.

Cada primeiro CMD deve explicar, em comentários, o valor recomendado, a finalidade e a obrigatoriedade de cada widget, inclusive quando deixá-lo vazio. Os CMDs seguintes explicam o que executam e o resultado esperado. A célula final orienta exportação com outputs, commit e revisão de evidências.

Revalidação das melhorias: executar e revisar um notebook por vez, na ordem 00 → 01 → 02 → 03. Usar os novos run_ids de 02 em 03, em nova sessão Python. Preservar exports anteriores; arquivar novos exports revisados com manifesto e hashes após recebimento. Código atualizado não equivale a execução validada.
