"""Contrato de origem v1. Tipagem/DQ serão aplicadas na Prata."""

CONTRACTS = {
    "clientes_cdc": ("id_cliente", "cpf", "nome", "cidade", "estado", "renda", "segmento", "data_atualizacao", "operacao"),
    "contas_cdc": ("id_conta", "id_cliente", "tipo_conta", "status_conta", "data_abertura", "data_atualizacao", "operacao"),
    "cartoes_cdc": ("id_cartao", "id_conta", "tipo_cartao", "limite", "status_cartao", "data_atualizacao", "operacao"),
    "transacoes": ("id_transacao", "id_cartao", "data_transacao", "valor", "mcc", "estabelecimento", "canal", "pais", "moeda"),
    "eventos_risco": ("id_evento", "id_transacao", "tipo_evento", "severidade", "data_evento"),
    "estornos": ("id_estorno", "id_transacao", "data_estorno", "motivo", "valor_estorno"),
}

SCHEMA_VERSION = 1
