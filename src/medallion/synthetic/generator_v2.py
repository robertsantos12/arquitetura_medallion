"""Cenário V2 da vila: ampliação determinística das seis fontes do contrato original."""
import csv
import io
import json
from datetime import date, datetime, timedelta, timezone
from medallion.synthetic.generator import gerar_lotes as gerar_v1
from medallion.synthetic.contracts import CONTRACTS

PERSONAGENS = [
    ("CHAVES", "Chaves", 150), ("MADRUGA", "Seu Madruga", 900),
    ("FLORINDA", "Dona Florinda", 5200), ("GIRAFALES", "Professor Girafales", 8200),
    ("BARRIGA", "Seu Barriga", 12000), ("QUICO", "Quico", 1800),
    ("CHIQUINHA", "Chiquinha", 200), ("BRUXA71", "Dona Clotilde", 3200),
    ("NHONHO", "Nhonho", 2800), ("POPO", "Pópis", 700),
    ("GODINEZ", "Godínez", 1100), ("JAIMINHO", "Jaiminho", 2100),
    ("PATY", "Paty", 1800), ("GLORIA", "Glória", 4500),
    ("MALICHA", "Malicha", 900), ("HECTOR", "Héctor", 3000),
    ("ROMAN", "Román", 3500), ("VALDES", "Valdés", 2200),
]

def gerar_lotes_v2(data_referencia="2026-01-15", dias=120, transacoes_por_dia=100):
    """Mantém os casos v1, acrescenta 18 personagens e 12 mil transações narrativas."""
    base = date.fromisoformat(data_referencia)
    if base.isoformat() != data_referencia:
        raise ValueError("Use YYYY-MM-DD")
    if dias < 14 or transacoes_por_dia < len(PERSONAGENS):
        raise ValueError("Parâmetros insuficientes para os cenários")
    lotes = gerar_v1(data_referencia)
    inicial, segundo, atrasado = (lotes[k] for k in ("01_inicial", "02_incremental", "03_atrasado"))
    def instante(d, hora=12):
        return datetime.combine(base + timedelta(days=d), datetime.min.time(), timezone.utc).replace(hour=hora).isoformat()
    for codigo, nome, renda in PERSONAGENS:
        cid, aid, kid = "C_"+codigo, "A_"+codigo, "K_"+codigo
        inicial["clientes_cdc"].append(dict(id_cliente=cid, cpf="CPF_SINTETICO_"+codigo,
            nome=nome, cidade="Vila do Chaves", estado="SP", renda=f"{renda:.2f}",
            segmento="FICTICIO", data_atualizacao=instante(-130), operacao="I"))
        inicial["contas_cdc"].append(dict(id_conta=aid, id_cliente=cid, tipo_conta="CORRENTE",
            status_conta="ATIVA", data_abertura=(base-timedelta(days=150)).isoformat(),
            data_atualizacao=instante(-130), operacao="I"))
        inicial["cartoes_cdc"].append(dict(id_cartao=kid, id_conta=aid,
            tipo_cartao="DEBITO" if codigo in ("MADRUGA","CHAVES") else "CREDITO",
            limite=f"{max(100,renda * 2):.2f}", status_cartao="ATIVO",
            data_atualizacao=instante(-130), operacao="I"))
    def tx(id_, codigo, dia, valor, loja, mcc, status="APROVADA", motivo="", hora=12):
        return dict(id_transacao=id_, id_cartao="K_"+codigo,
            data_transacao=instante(dia,hora), valor=f"{valor:.2f}", mcc=mcc,
            estabelecimento=loja, canal="POS", pais="BR", moeda="BRL",
            status_transacao=status, motivo_recusa=motivo,
            cenario="VILA_CHAVES_V2")
    for d in range(dias):
        lote = inicial if d < 60 else (segundo if d < 105 else atrasado)
        destino = lote["transacoes"]
        for i in range(transacoes_por_dia):
            cod, _, renda = PERSONAGENS[(d*7+i)%len(PERSONAGENS)]
            valor = 5 + ((d*37+i*19)%2200)/10
            destino.append(tx(f"V2_{d:03d}_{i:03d}",cod,d,valor,
                ("Mercearia da Vila","Padaria","Farmácia","Papelaria","Restaurante")[i%5],
                ("5411","5462","5912","5943","5812")[i%5]))
        # Eventos correlacionados explicitamente em dias alternados.
        if d%2==0:
            destino.append(tx(f"V2_CAFE_{d:03d}","FLORINDA",d,26.90,
                              "Café e Biscoitos da Vila","5499",hora=9))
            destino.append(tx(f"V2_ROSAS_{d:03d}","GIRAFALES",d,79.90,
                              "Floricultura das Rosas","5992",hora=10))
        if d%30==4:
            destino.append(tx(f"V2_ALUGUEL_REC_{d:03d}","MADRUGA",d,650.00,
                              "Aluguel Seu Barriga","6513","RECUSADA",
                              "SALDO_INSUFICIENTE"))
            destino.append(tx(f"V2_ALUGUEL_PAGO_{d:03d}","BARRIGA",d,650.00,
                              "Recebimento Aluguel da Vila","6513"))
        if d%7==1:
            destino.append(tx(f"V2_PIRULITO_{d:03d}","CHAVES",d,3.50,
                              "Venda de Pirulitos","5441","RECUSADA",
                              "LIMITE_INSUFICIENTE"))
    # Caso de risco e estorno vinculados a transação nova aprovada.
    segundo["eventos_risco"].append(dict(id_evento="V2_EVENTO_RISCO",id_transacao="V2_065_000",
        tipo_evento="SUSPEITA",severidade="ALTA",data_evento=instante(66)))
    atrasado["estornos"].append(dict(id_estorno="V2_ESTORNO",id_transacao="V2_065_000",
        data_estorno=instante(110),motivo="PARCIAL",valor_estorno="5.00"))
    return lotes

def arquivos_planejados_v2(data_referencia="2026-01-15"):
    arquivos = {}
    for lote, fontes in gerar_lotes_v2(data_referencia).items():
        for fonte, rows in fontes.items():
            if not rows:
                continue
            if fonte.endswith("_cdc"):
                data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True)+"\n" for r in rows).encode()
                arquivos[f"{lote}/{fonte}/dados.json"] = (data,len(rows),fonte,lote)
                continue
            grupos = {}
            for row in rows:
                part = row["data_transacao"][:10] if fonte=="transacoes" else ""
                grupos.setdefault(part,[]).append(row)
            for part, registros in grupos.items():
                colunas = list(CONTRACTS[fonte]) + sorted(set().union(*(r.keys() for r in registros))-set(CONTRACTS[fonte]))
                out = io.StringIO(newline="")
                escritor = csv.DictWriter(out, fieldnames=colunas, lineterminator="\n")
                escritor.writeheader()
                escritor.writerows(registros)
                nome = f"{lote}/{fonte}/" + (f"data={part}/" if part else "") + "dados.csv"
                arquivos[nome] = (out.getvalue().encode(),len(registros),fonte,lote)
    return arquivos
