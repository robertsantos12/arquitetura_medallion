# Contrato Bronze 13 validado por export

Seis views retornaram METADADOS BRONZE: OK e CONTRATO BRONZE: OK. Contagens: clientes 24, contas 23, cartões 24, transações 12.158, risco 4 e estornos 4. De acordo com o módulo executado, houve reconciliação do manifesto/Bronze antes e depois e comparação dos campos derivados por linha.

Metadados expostos em views persistentes, preservando raw e snapshots. batch_id representa lote lógico legado derivado; não houve recuperação do UUID configurado no 05 nem adição física dessas colunas às raw. O contrato lógico está validado; manter a distinção no PR/defesa. Esta execução não comprova repetição do notebook 13, apenas criação/leitura e verificações reportadas.

Export sanitizado, parâmetros e hashes no manifesto. Análise por arquivo enviado, sem acesso direto ao workspace. Evidências anteriores preservadas. Linhagem 12 permanece bloqueada por permissão.
