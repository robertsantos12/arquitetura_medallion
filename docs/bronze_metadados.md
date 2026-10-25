# Contrato aditivo de metadados Bronze

## Motivação e semântica

O 05 usa uuid4 para run_id e não persiste o batch_id configurado no registro raw. Não há evidência suficiente para recuperar esse UUID original para todas as linhas: não substituir run_id por batch_id nem inventar correlação com uma auditoria inexistente.

O complemento 13 cria seis views persistentes no schema Bronze, raw_<fonte>_contrato_v2. Mantém todas as colunas raw e acrescenta:

|Metadado|Definição|
|---|---|
|arquivo_origem|Caminho completo do arquivo no Volume: raiz/cenarios/v2/data_referencia/arquivo relativo|
|data_ingestao|DATE derivada do timestamp original ingerido_em, em sessão UTC|
|timestamp_ingestao|O próprio ingerido_em original, não horário de execução da view|
|batch_id|SHA256 UTF-8 de v2 + separador barra vertical + data_referencia + separador + lote; identifica lote lógico de ingestão, comum aos arquivos do mesmo lote|
|batch_id_origem|DERIVADO_CENARIO_DATA_LOTE_LEGADO: proveniência explícita, não UUID configurado no 05|
|hash_linha|SHA256 UTF-8 do payload_json canônico já preservado na Bronze; duplicatas com conteúdo idêntico têm mesmo hash, mesmo que id_registro posicional seja diferente|
|schema_version|Versão do contrato obtida do manifesto V2 validado, nesta fixture 1; não é versão do log Delta nem número de campos presentes|

run_id continua como tentativa que inseriu originalmente a linha. batch_id derivado é identidade lógica do lote, não tentativa. Valor de negócio inválido permanece no payload. hash_linha não é checksum dos bytes originais da linha CSV: essa integridade é de arquivo_sha256, mantida separadamente. schema_version 1 designa contrato compatível com campos adicionais; não afirma que todos os arquivos têm cabeçalhos iguais.

## Segurança e compatibilidade

Nenhum ALTER/UPDATE/DELETE nas raw, nem alteração de massa, manifesto ou snapshots. O 13 exige Bronze completa e reconciliada, schema existente e CREATE VIEW/SELECT. Sessão UTC obrigatória. Views são limitadas à data_referencia homologada para evitar associar versão sem validar manifesto de outras massas. Objeto existente só é reutilizado se a definição corresponder; não há CREATE OR REPLACE. Outra data/migração exige nova versão de view. Definição não visível ou divergente bloqueia sem overwrite.

Após DDL, releitura de todas as linhas compara hashes com hashlib, batch lógico, timestamps, versão e caminho; recontagem com a Bronze e nova reconciliação do manifesto confirmam preservação. Falha parcial pode deixar algumas views criadas; preservar output e retomar com mesmos parâmetros, sem apagar objetos.

## Aplicação

Pull, nova sessão Python e notebook 13_completar_metadados_bronze. CMD 1: catalogo=workspace e data_referencia=2026-01-15. CMDs 2–3. Esperado seis METADADOS BRONZE: OK e CONTRATO BRONZE: OK. Exportar com outputs, fazer commit e enviar para revisão antes do merge. Não repetir ingestão ou transformação. O PR aberto acompanha commits da mesma branch automaticamente.

## Estado e ressalvas para o PDF

IMPLEMENTADO: contrato lógico completo de metadados em views persistentes. TESTADO LOCALMENTE: semântica SQL, batch diferente de run_id, hash de conteúdo, validação de parâmetros e sintaxe; suite combinada 43 testes aprovados. VALIDADO: criação/leitura real nas seis views, conforme export do 13 em docs/evidencias/2026-10-25_metadados_bronze_13. As colunas novas NÃO estão materializadas nas tabelas raw; essa distinção deve permanecer na revisão e na defesa. O complemento não recupera o batch_id configurado historicamente. Se a avaliação exigir metadados físicos ou o UUID original, a lacuna correspondente permanece e exige migração compatível/novo contrato de escrita, sem alegar recuperação impossível.

V2 solução: persistir explicitamente batch lógico e tentativa no ingestor, versão por arquivo/contrato, hash canônico de conteúdo e verificação antes dos matches; migrar consumidores para contrato enriquecido mediante regressão e documentação. Para streaming, identity tópico/partição/offset/event_id deve permanecer separada de batch_id e hash de conteúdo.
