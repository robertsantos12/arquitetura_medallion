"""Fixtures determinísticas. Sem dados reais ou dependência de Spark."""

import csv
import io
import json
from datetime import date, datetime, timedelta, timezone

from medallion.synthetic.contracts import CONTRACTS


def gerar_lotes(data_referencia="2026-01-15"):
    """Três chegadas; data de negócio pode anteceder a chegada do registro."""
    base = date.fromisoformat(data_referencia)
    if base.isoformat() != data_referencia:
        raise ValueError("Use YYYY-MM-DD")

    def ts(dias=0):
        return datetime.combine(base + timedelta(days=dias), datetime.min.time(), timezone.utc).isoformat()

    def cliente(id, **changes):
        # Tokens deliberadamente inválidos como documentos pessoais: nunca CPFs reais.
        return dict(id_cliente=id, cpf=f"CPF_SINTETICO_{id}", nome=f"Cliente Sintetico {id}",
                    cidade="Porto Alegre", estado="RS", renda="5000.00", segmento="VAREJO",
                    data_atualizacao=ts(-40), operacao="I", **changes)

    def conta(id, cli):
        return dict(id_conta=id, id_cliente=cli, tipo_conta="CORRENTE", status_conta="ATIVA",
                    data_abertura=(base-timedelta(days=60)).isoformat(), data_atualizacao=ts(-40), operacao="I")

    def cartao(id, conta):
        return dict(id_cartao=id, id_conta=conta, tipo_cartao="CREDITO", limite="5000.00",
                    status_cartao="ATIVO", data_atualizacao=ts(-40), operacao="I")

    def tx(id, card, dias, valor, **changes):
        row = dict(id_transacao=id, id_cartao=card, data_transacao=ts(dias), valor=valor,
                   mcc="5411", estabelecimento="Mercado Sintetico", canal="POS", pais="BR",
                   moeda="BRL", status_transacao="APROVADA")
        row.update(changes)
        return row

    c1, c2 = cliente("C001"), cliente("C002")
    a1, a2, a3 = conta("A001", "C001"), conta("A002", "C001"), conta("A003", "C002")
    k1, k2, k3 = cartao("K001", "A001"), cartao("K002", "A002"), cartao("K003", "A003")
    t1 = tx("T001", "K001", 0, "100.00")
    inicial = {
        "clientes_cdc": [c1, c2, dict(c1), dict(cliente("C_BAD"), renda="nao_numerico", estado="XX")],
        "contas_cdc": [a1, a2, a3, conta("A_BAD", "C_INEXISTENTE")],
        "cartoes_cdc": [k1, k2, k3, cartao("K_BAD", "A_INEXISTENTE")],
        "transacoes": [t1, dict(t1), tx("T002", "K002", 0, "200.00"),
                       tx("T003", "K003", 0, "300.00"), tx("T_NEG", "K001", 0, "-10.00"),
                       tx("T_BAD_CARD", "K_INEXISTENTE", 0, "20.00"),
                       tx("T_CANCEL", "K001", 0, "90.00", status_transacao="CANCELADA")],
        "eventos_risco": [dict(id_evento="E001", id_transacao="T003", tipo_evento="SUSPEITA", severidade="ALTA", data_evento=ts(1))],
        "estornos": [dict(id_estorno="S001", id_transacao="T002", data_estorno=ts(1), motivo="PARCIAL", valor_estorno="50.00")],
    }
    segundo = {
        "clientes_cdc": [dict(c1, cidade="Canoas", renda="6500.00", data_atualizacao=ts(2), operacao="U")],
        "contas_cdc": [dict(a2, status_conta="ENCERRADA", data_atualizacao=ts(2), operacao="U")],
        "cartoes_cdc": [dict(k1, limite="8000.00", data_atualizacao=ts(2), operacao="U"),
                        dict(k2, status_cartao="CANCELADO", data_atualizacao=ts(2), operacao="U")],
        "transacoes": [dict(t1), tx("T004", "K001", 3, "400.00", dispositivo="APP_SINTETICO"),
                       tx("T005", "K002", 3, "80.00", dispositivo="APP_SINTETICO"),
                       tx("T006", "K003", 32, "1500.00", dispositivo="APP_SINTETICO")],
        "eventos_risco": [dict(id_evento="E002", id_transacao="T003", tipo_evento="CHARGEBACK", severidade="ALTA", data_evento=ts(3)),
                          dict(id_evento="E_BAD", id_transacao="T_INEXISTENTE", tipo_evento="FRAUDE", severidade="ALTA", data_evento=ts(3))],
        "estornos": [dict(id_estorno="S002", id_transacao="T003", data_estorno=ts(3), motivo="TOTAL", valor_estorno="300.00"),
                     dict(id_estorno="S_BAD", id_transacao="T_INEXISTENTE", data_estorno=ts(3), motivo="TOTAL", valor_estorno="10.00")],
    }
    terceiro = {
        "clientes_cdc": [dict(c1, segmento="ALTA_RENDA", data_atualizacao=ts(1), operacao="U")],
        "contas_cdc": [], "cartoes_cdc": [],
        "transacoes": [tx("T007", "K001", 1, "70.00", dispositivo="POS_SINTETICO"),
                       tx("T008", "K003", -31, "50.00", dispositivo="POS_SINTETICO")],
        "eventos_risco": [], "estornos": [],
    }
    return {"01_inicial": inicial, "02_incremental": segundo, "03_atrasado": terceiro}


def arquivos_planejados(data_referencia="2026-01-15"):
    """Retorna caminho relativo -> (bytes, quantidade, fonte, lote)."""
    result = {}
    for lote, fontes in gerar_lotes(data_referencia).items():
        for fonte, rows in fontes.items():
            if not rows:
                continue
            if fonte.endswith("_cdc"):
                content = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True)+"\n" for r in rows)
                result[f"{lote}/{fonte}/dados.json"] = (content.encode(), len(rows), fonte, lote)
            else:
                # Transações particionadas pela data de negócio; lote controla chegada.
                groups = {}
                for r in rows:
                    part = r["data_transacao"][:10] if fonte == "transacoes" else ""
                    groups.setdefault(part, []).append(r)
                for part, records in groups.items():
                    fields = list(CONTRACTS[fonte]) + sorted(set().union(*(r.keys() for r in records))-set(CONTRACTS[fonte]))
                    out = io.StringIO(newline="")
                    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
                    writer.writeheader(); writer.writerows(records)
                    path = f"{lote}/{fonte}/" + (f"data={part}/" if part else "") + "dados.csv"
                    result[path] = (out.getvalue().encode(), len(records), fonte, lote)
    return result
